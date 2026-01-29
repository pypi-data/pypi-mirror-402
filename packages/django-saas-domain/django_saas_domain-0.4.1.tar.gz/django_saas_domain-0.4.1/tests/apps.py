from django.apps import AppConfig


class TestConfig(AppConfig):
    name = 'tests'

    def ready(self):
        __import__('saas_base.registry.default_roles')
        __import__('saas_domain.registry.default_roles')
