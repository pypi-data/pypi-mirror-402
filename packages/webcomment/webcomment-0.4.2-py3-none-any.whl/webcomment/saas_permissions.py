from django.utils.translation import gettext_lazy as _
from saas_base.registry import Severity, perm_registry

perm_registry.register_permission(
    key='content.comment.view',
    label=_('View Comments'),
    module='Content',
    description=_('Can read comments on resources'),
    severity=Severity.LOW,
)

perm_registry.register_permission(
    key='content.comment.manage',
    label=_('Moderate Comments'),
    module='Content',
    description=_("Can delete or hide any user's comments"),
    severity=Severity.HIGH,
)

perm_registry.register_permission(
    key='content.comment.settings',
    label=_('Manage Comment Settings'),
    module='Content',
    description=_('Can change comment settings'),
    severity=Severity.HIGH,
)
