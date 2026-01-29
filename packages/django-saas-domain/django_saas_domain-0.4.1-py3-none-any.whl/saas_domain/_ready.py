from django.apps import apps
from django.core.checks import Error, register
from django.db.models.signals import pre_delete

from .models import Domain
from .providers import get_domain_provider


def remove_domain(sender, instance: Domain, **kwargs):
    provider = get_domain_provider(instance.provider)
    if provider:
        provider.remove_domain(instance)


pre_delete.connect(remove_domain, sender=Domain)


def register_checks():
    def check(app_configs, **kwargs):
        if not apps.is_installed('saas_base'):
            return [Error("'saas_base' must be in INSTALLED_APPS.")]
        else:
            return []

    register(check, 'saas')
