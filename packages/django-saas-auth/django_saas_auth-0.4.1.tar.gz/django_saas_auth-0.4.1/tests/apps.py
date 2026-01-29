from django.apps import AppConfig


class TestsConfig(AppConfig):
    name = 'tests'

    def ready(self):
        __import__('saas_base.registry.default_roles')
        __import__('saas_base.registry.default_scopes')
