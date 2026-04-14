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
        return Response(status=status.HTTP_201_CREATED)


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
        import unicodedata
        import pandas as pd

        file = request.FILES.get('file')
        if not file:
            return Response({'message': 'No se proporcionó archivo'}, status=status.HTTP_400_BAD_REQUEST)

        name = file.name.lower()
        try:
            if name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file, dtype=str)
            elif name.endswith('.csv'):
                df = pd.read_csv(file, dtype=str, encoding='utf-8-sig')
            else:
                return Response({'message': 'Formato no soportado. Use .csv o .xlsx'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': f'Error al leer el archivo: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        def normalize(s):
            return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower().strip()

        df.columns = [normalize(c) for c in df.columns]

        col_map = {
            'date':     ['fecha', 'date'],
            'desc':     ['descripcion', 'desc', 'description', 'concepto', 'detalle'],
            'amount':   ['monto', 'amount', 'importe', 'valor'],
            'type':     ['tipo', 'type'],
            'category': ['categoria', 'category', 'cat'],
        }

        def find_col(field):
            for alias in col_map[field]:
                if alias in df.columns:
                    return alias
            return None

        col_date     = find_col('date')
        col_desc     = find_col('desc')
        col_amount   = find_col('amount')
        col_type     = find_col('type')
        col_category = find_col('category')

        if not col_desc or not col_amount:
            return Response({
                'message': 'Columnas no reconocidas. El archivo debe tener: Fecha, Descripción, Monto, Tipo, Categoría'
            }, status=status.HTTP_400_BAD_REQUEST)

        imported = 0
        skipped = 0
        errors = []
        to_create = []

        for idx, row in df.iterrows():
            row_num = idx + 2

            desc = str(row.get(col_desc, '')).strip()
            if not desc or desc == 'nan':
                errors.append({'row': row_num, 'msg': 'Descripción vacía'})
                skipped += 1
                continue

            try:
                amount_raw = str(row.get(col_amount, '')).replace('$', '').replace(',', '').strip()
                amount = Decimal(amount_raw)
                if amount <= 0:
                    raise ValueError()
            except (ValueError, InvalidOperation):
                errors.append({'row': row_num, 'msg': 'Monto inválido'})
                skipped += 1
                continue

            raw_type = str(row.get(col_type, 'gasto')).lower().strip() if col_type else 'gasto'
            tx_type = 'ingreso' if raw_type.startswith('i') else 'gasto'

            category = str(row.get(col_category, 'Otros')).strip() if col_category else 'Otros'
            if not category or category == 'nan':
                category = 'Otros'

            tx_date = date.today()
            if col_date:
                try:
                    import pandas as pd
                    tx_date = pd.to_datetime(str(row.get(col_date, '')), dayfirst=False).date()
                except Exception:
                    pass

            to_create.append(Transaction(
                user=request.user,
                desc=desc,
                amount=amount,
                type=tx_type,
                category=category,
                date=tx_date,
            ))
            imported += 1

        if to_create:
            Transaction.objects.bulk_create(to_create)

        return Response({'imported': imported, 'skipped': skipped, 'errors': errors})


class TransactionTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output)
        writer.writerow(['Fecha', 'Descripción', 'Monto', 'Tipo', 'Categoría'])
        writer.writerow(['2026-04-14', 'Ejemplo supermercado', '350.00', 'gasto', 'Alimentación'])
        writer.writerow([])
        writer.writerow(['--- Categorías disponibles (usar exactamente como aparecen) ---'])
        writer.writerow(['Tipo válido: ingreso | gasto'])
        writer.writerow([])
        for cat in CATEGORY_DEFAULTS:
            writer.writerow(['', '', '', '', cat])

        resp = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="finanzly-plantilla.csv"'
        return resp


class TransactionExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fmt = request.query_params.get('format', 'csv').lower()
        transactions = Transaction.objects.filter(user=request.user).order_by('-date')

        if fmt == 'csv':
            return self._export_csv(transactions)
        elif fmt == 'pdf':
            return self._export_pdf(transactions, request.user)
        return Response({'message': 'Formato no soportado. Usa ?format=csv o ?format=pdf'}, status=status.HTTP_400_BAD_REQUEST)

    def _export_csv(self, transactions):
        output = io.StringIO()
        output.write('\ufeff')  # BOM para compatibilidad con Excel
        writer = csv.writer(output)
        writer.writerow(['Fecha', 'Descripción', 'Monto', 'Tipo', 'Categoría'])
        for t in transactions:
            writer.writerow([
                t.date.strftime('%Y-%m-%d') if t.date else '',
                t.desc,
                f'{t.amount:.2f}',
                t.type,
                t.category or 'Otros',
            ])

        # Sección de referencia: categorías válidas
        writer.writerow([])
        writer.writerow(['--- Categorías disponibles (usar exactamente como aparecen) ---'])
        writer.writerow(['Tipo válido: ingreso | gasto'])
        writer.writerow([])
        for cat in CATEGORY_DEFAULTS:
            writer.writerow(['', '', '', '', cat])

        resp = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="finanzly-transacciones.csv"'
        return resp

    def _export_pdf(self, transactions, user):
        from weasyprint import HTML
        from django.template.loader import render_to_string

        ingresos = sum(t.amount for t in transactions if t.type == 'ingreso')
        gastos = sum(t.amount for t in transactions if t.type == 'gasto')
        balance = ingresos - gastos

        html_string = render_to_string('transactions/export_pdf.html', {
            'transactions': transactions,
            'summary': {'ingresos': ingresos, 'gastos': gastos, 'balance': balance},
            'user': user,
            'today': date.today().strftime('%d de %B de %Y'),
        })

        pdf_bytes = HTML(string=html_string).write_pdf()
        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="finanzly-reporte.pdf"'
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
