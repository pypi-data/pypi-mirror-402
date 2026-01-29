from django.core.signals import setting_changed
from saas_base.settings import BaseSettings


class AuthSettings(BaseSettings):
    SETTINGS_KEY = 'SAAS_AUTH'
    DEFAULT_SETTINGS = {
        'LOCATION_RESOLVER': {
            'backend': 'saas_auth.location.cloudflare.CloudflareBackend',
        },
        'SESSION_RECORD_INTERVAL': 300,
    }
    IMPORT_SETTINGS = [
        'LOCATION_RESOLVER',
    ]


auth_settings = AuthSettings()
setting_changed.connect(auth_settings.listen_setting_changed)
