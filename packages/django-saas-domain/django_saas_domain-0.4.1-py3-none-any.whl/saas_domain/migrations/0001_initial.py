import uuid

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.SAAS_TENANT_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('provider', models.CharField(max_length=100)),
                ('hostname', models.CharField(max_length=100, unique=True)),
                ('verified', models.BooleanField(default=False, editable=False)),
                ('ssl', models.BooleanField(default=False, editable=False)),
                ('active', models.BooleanField(default=False, editable=False)),
                ('instrument_id', models.CharField(blank=True, editable=False, max_length=256, null=True)),
                ('instrument', models.JSONField(blank=True, editable=False, null=True)),
                ('created_at', models.DateTimeField(default=timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(on_delete=models.CASCADE, to=settings.SAAS_TENANT_MODEL)),
            ],
            options={
                'verbose_name': 'domain',
                'verbose_name_plural': 'domains',
                'db_table': 'saas_domain',
                'ordering': ['created_at'],
            },
        ),
    ]
