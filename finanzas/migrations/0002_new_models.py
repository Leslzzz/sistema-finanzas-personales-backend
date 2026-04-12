import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Drop old models in dependency order ────────────────────────────
        # Income and Outcome reference Transaction, so delete them first.
        migrations.DeleteModel(name='Income'),
        migrations.DeleteModel(name='Outcome'),
        # Transaction references Category, so delete Transaction before Category.
        migrations.DeleteModel(name='Transaction'),
        migrations.DeleteModel(name='Category'),

        # ── Create new Transaction ─────────────────────────────────────────
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('desc', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('type', models.CharField(choices=[('ingreso', 'Ingreso'), ('gasto', 'Gasto')], max_length=10)),
                ('category', models.CharField(blank=True, max_length=100, null=True)),
                ('date', models.DateField()),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-date']},
        ),

        # ── Create new Budget ──────────────────────────────────────────────
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=100)),
                ('icon', models.CharField(max_length=10)),
                ('color', models.CharField(max_length=7)),
                ('limit', models.DecimalField(decimal_places=2, max_digits=12)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
