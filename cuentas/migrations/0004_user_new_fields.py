from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cuentas', '0003_alter_user_email_alter_user_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar_url',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='timezone',
            field=models.CharField(default='America/Mexico_City', max_length=50),
        ),
        migrations.AddField(
            model_name='user',
            name='month_start_day',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='user',
            name='budget_alert',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='daily_reminder',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='monthly_income',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='onboarding_completed',
            field=models.BooleanField(default=False),
        ),
    ]
