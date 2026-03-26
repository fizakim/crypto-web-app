from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone

def backfill_price_history(apps, schema_editor):
    Cryptocurrency = apps.get_model('crypto', 'Cryptocurrency')
    PriceHistory = apps.get_model('crypto', 'PriceHistory')

    for crypto in Cryptocurrency.objects.all():
        PriceHistory.objects.create(
            cryptocurrency=crypto,
            price=crypto.current_price,
            recorded_at=crypto.price_updated_at or timezone.now(),
        )

class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('recorded_at', models.DateTimeField(db_index=True, default=timezone.now)),
                ('cryptocurrency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_history', to='crypto.cryptocurrency')),
            ],
            options={
                'ordering': ['recorded_at'],
            },
        ),
        migrations.RunPython(backfill_price_history, migrations.RunPython.noop),
    ]