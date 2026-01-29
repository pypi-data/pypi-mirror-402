from django.utils.translation import gettext_lazy as _
from saas_base.registry import Severity, perm_registry

perm_registry.register_permission(
    key='user.session.view',
    label=_('View Sessions'),
    module='User',
    description=_('List all active sessions for the user'),
    severity=Severity.NORMAL,
)

perm_registry.register_permission(
    key='user.session.manage',
    label=_('Manage Sessions'),
    module='User',
    description=_('Delete any active sessions for the user'),
    severity=Severity.HIGH,
)

perm_registry.register_permission(
    key='user.token.view',
    label=_('View Tokens'),
    module='User',
    description=_('List all API tokens for the user'),
    severity=Severity.NORMAL,
)

perm_registry.register_permission(
    key='user.token.manage',
    label=_('Manage Tokens'),
    module='User',
    description=_('Add, update, delete any API tokens for the user'),
    severity=Severity.CRITICAL,
)

# security permissions will not distribute to token scopes

perm_registry.register_permission(
    key='security.mfa.view',
    label=_('View MFA settings'),
    module='Security',
    severity=Severity.HIGH,
)

perm_registry.register_permission(
    key='security.mfa.manage',
    label=_('Verify MFA'),
    module='Security',
    severity=Severity.CRITICAL,
)

perm_registry.register_permission(
    key='security.mfa.verify',
    label=_('Verify MFA'),
    module='Security',
    severity=Severity.CRITICAL,
)
