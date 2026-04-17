from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0002_new_models'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MonthlyPeriod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('monthly_income', models.DecimalField(decimal_places=2, max_digits=12)),
                ('status', models.CharField(choices=[('active', 'Active'), ('closed', 'Closed')], default='active', max_length=10)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='periods', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-year', '-month'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='monthlyperiod',
            unique_together={('user', 'year', 'month')},
        ),
        migrations.AddField(
            model_name='transaction',
            name='period',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='transactions',
                to='finanzas.monthlyperiod',
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='period',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='budgets',
                to='finanzas.monthlyperiod',
            ),
        ),
    ]
