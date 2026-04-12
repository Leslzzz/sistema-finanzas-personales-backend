import csv
import io
import calendar
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db.models import Sum
from django.http import HttpResponse

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .models import Transaction, Budget


# ── Category defaults ──────────────────────────────────────────────────────────

CATEGORY_DEFAULTS = {
    'Vivienda':      {'icon': '🏠', 'color': '#60a5fa'},
    'Alimentación':  {'icon': '🍔', 'color': '#34d399'},
    'Transporte':    {'icon': '🚗', 'color': '#fbbf24'},
    'Salud':         {'icon': '💊', 'color': '#f87171'},
    'Ocio':          {'icon': '🎬', 'color': '#a78bfa'},
    'Educación':     {'icon': '📚', 'color': '#38bdf8'},
    'Ropa':          {'icon': '👕', 'color': '#fb7185'},
    'Servicios':     {'icon': '💡', 'color': '#a3e635'},
    'Ahorro':        {'icon': '💰', 'color': '#4ade80'},
    'Otros':         {'icon': '📦', 'color': '#94a3b8'},
}


# ── Helper: active month range ─────────────────────────────────────────────────

def get_active_month_range(user):
    today = date.today()
    day = user.month_start_day

    if today.day >= day:
        start_month, start_year = today.month, today.year
    elif today.month == 1:
        start_month, start_year = 12, today.year - 1
    else:
        start_month, start_year = today.month - 1, today.year

    max_day_start = calendar.monthrange(start_year, start_month)[1]
    start = date(start_year, start_month, min(day, max_day_start))

    if start_month == 12:
        end_month, end_year = 1, start_year + 1
    else:
        end_month, end_year = start_month + 1, start_year

    max_day_end = calendar.monthrange(end_year, end_month)[1]
    if day == 1:
        end = date(end_year, end_month, max_day_end)
    else:
        end = date(end_year, end_month, min(day - 1, max_day_end))

    return start, end


def _tx_dict(t):
    return {
        'id': str(t.id),
        'desc': t.desc,
        'amount': float(t.amount),
        'type': t.type,
        'category': t.category,
        'date': t.date.strftime('%Y-%m-%d'),
    }


def _budget_dict(b, spent):
    return {
        'id': str(b.id),
        'label': b.label,
        'icon': b.icon,
        'color': b.color,
        'limit': float(b.limit),
        'spent': float(spent),
    }


# ── Onboarding ─────────────────────────────────────────────────────────────────

class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        monthly_income = request.data.get('monthlyIncome')
        categories = request.data.get('categories', [])

        if monthly_income is not None:
            user.monthly_income = Decimal(str(monthly_income))

        for cat in categories:
            label = cat.get('label', '')
            budget_limit = cat.get('budgetLimit', 0)
            defaults = CATEGORY_DEFAULTS.get(label, {'icon': '📦', 'color': '#94a3b8'})
            Budget.objects.create(
                user=user,
                label=label,
                icon=defaults['icon'],
                color=defaults['color'],
                limit=Decimal(str(budget_limit)),
            )

        user.onboarding_completed = True
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Transactions ───────────────────────────────────────────────────────────────

class TransactionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        txs = Transaction.objects.filter(user=request.user).order_by('-date')
        return Response([_tx_dict(t) for t in txs])

    def post(self, request):
        desc = request.data.get('desc')
        amount = request.data.get('amount')
        type_ = request.data.get('type')
        category = request.data.get('category')
        date_str = request.data.get('date')

        if type_ not in ('ingreso', 'gasto'):
            return Response({'message': 'type debe ser "ingreso" o "gasto"'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValueError()
        except (ValueError, InvalidOperation):
            return Response({'message': 'amount debe ser un número positivo'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response({'message': 'date debe tener formato YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        t = Transaction.objects.create(
            user=request.user,
            desc=desc,
            amount=amount,
            type=type_,
            category=category,
            date=parsed_date,
        )
        return Response(_tx_dict(t), status=status.HTTP_201_CREATED)


class TransactionSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = get_active_month_range(request.user)
        qs = Transaction.objects.filter(user=request.user, date__range=(start, end))
        ingresos = qs.filter(type='ingreso').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        gastos = qs.filter(type='gasto').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        return Response({
            'ingresos': float(ingresos),
            'gastos': float(gastos),
            'balance': float(ingresos - gastos),
        })


class TransactionCategoriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start, end = get_active_month_range(request.user)
        gastos = Transaction.objects.filter(
            user=request.user,
            type='gasto',
            date__range=(start, end),
        )

        totals: dict[str, Decimal] = {}
        for t in gastos:
            cat = t.category or 'Otros'
            totals[cat] = totals.get(cat, Decimal('0')) + t.amount

        if not totals:
            return Response([])

        grand_total = sum(totals.values())
        budget_colors = {b.label: b.color for b in Budget.objects.filter(user=request.user)}

        result = []
        for label, amount in totals.items():
            color = budget_colors.get(label) or CATEGORY_DEFAULTS.get(label, {}).get('color', '#94a3b8')
            result.append({'label': label, 'value': round(float(amount) / float(grand_total) * 100), 'color': color})

        # Adjust rounding so values sum exactly to 100
        diff = 100 - sum(r['value'] for r in result)
        if diff and result:
            result[0]['value'] += diff

        return Response(result)


class TransactionImportView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'message': 'No se proporcionó archivo'}, status=status.HTTP_400_BAD_REQUEST)

        name = file.name.lower()
        try:
            if name.endswith('.csv'):
                imported = self._import_csv(request.user, file)
            elif name.endswith(('.xlsx', '.xls')):
                imported = self._import_excel(request.user, file)
            else:
                return Response({'message': 'Formato no soportado. Use .csv o .xlsx'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': f'Error al procesar archivo: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'imported': imported})

    def _import_csv(self, user, file):
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        return self._insert_rows(user, reader)

    def _import_excel(self, user, file):
        import openpyxl
        wb = openpyxl.load_workbook(file, read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return 0
        headers = [str(h).strip() for h in rows[0]]
        return self._insert_rows(user, (dict(zip(headers, r)) for r in rows[1:]))

    def _insert_rows(self, user, rows):
        to_create = []
        for row in rows:
            try:
                desc = str(row.get('desc', '')).strip()
                amount = Decimal(str(row.get('amount', 0)))
                type_ = str(row.get('type', '')).strip()
                category = str(row.get('category', '')).strip() or None
                date_str = str(row.get('date', '')).strip()
                if type_ not in ('ingreso', 'gasto') or amount <= 0:
                    continue
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                to_create.append(Transaction(
                    user=user, desc=desc, amount=amount,
                    type=type_, category=category, date=parsed_date,
                ))
            except Exception:
                continue
        Transaction.objects.bulk_create(to_create)
        return len(to_create)


class TransactionExportView(APIView):
    """Token comes as query param ?token=... because this is a direct browser download."""
    authentication_classes = []
    permission_classes = []

    def _authenticate_from_query(self, request):
        token = request.query_params.get('token')
        if not token:
            return None
        auth = JWTAuthentication()
        try:
            validated = auth.get_validated_token(token.encode('utf-8'))
            return auth.get_user(validated)
        except (TokenError, InvalidToken, Exception):
            return None

    def get(self, request):
        user = self._authenticate_from_query(request)
        if not user:
            return HttpResponse(status=401)

        fmt = request.query_params.get('format', 'csv').lower()
        transactions = Transaction.objects.filter(user=user).order_by('-date')

        if fmt == 'csv':
            return self._export_csv(transactions)
        elif fmt == 'pdf':
            return self._export_pdf(transactions)
        return HttpResponse(status=400)

    def _export_csv(self, transactions):
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="finanzly-export.csv"'
        writer = csv.writer(resp)
        writer.writerow(['id', 'desc', 'amount', 'type', 'category', 'date'])
        for t in transactions:
            writer.writerow([str(t.id), t.desc, float(t.amount), t.type, t.category or '', t.date.strftime('%Y-%m-%d')])
        return resp

    def _export_pdf(self, transactions):
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter)
        styles = getSampleStyleSheet()

        data = [['Descripción', 'Monto', 'Tipo', 'Categoría', 'Fecha']]
        for t in transactions:
            data.append([t.desc, f'${float(t.amount):,.2f}', t.type, t.category or '', t.date.strftime('%Y-%m-%d')])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))

        doc.build([Paragraph('Finanzly – Historial de Transacciones', styles['Title']), table])
        buf.seek(0)

        resp = HttpResponse(buf.read(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="finanzly-export.pdf"'
        return resp


# ── Budgets ────────────────────────────────────────────────────────────────────

class BudgetListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        start, end = get_active_month_range(user)
        budgets = Budget.objects.filter(user=user)

        result = []
        for b in budgets:
            spent = Transaction.objects.filter(
                user=user, type='gasto', category=b.label, date__range=(start, end),
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            result.append(_budget_dict(b, spent))
        return Response(result)


class BudgetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        user = request.user
        try:
            budget = Budget.objects.get(id=pk, user=user)
        except Budget.DoesNotExist:
            return Response({'message': 'Presupuesto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        new_limit = request.data.get('limit')
        if new_limit is not None:
            budget.limit = Decimal(str(new_limit))
            budget.save()

        start, end = get_active_month_range(user)
        spent = Transaction.objects.filter(
            user=user, type='gasto', category=budget.label, date__range=(start, end),
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return Response(_budget_dict(budget, spent))
