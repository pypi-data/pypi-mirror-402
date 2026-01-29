from django.utils.translation import gettext_lazy as _
from saas_base.registry import perm_registry

perm_registry.register_permission(
    key='security.domain.view',
    label=_('View Domain'),
    module='Security',
    description=_('Can view the list of custom domains and their verification status'),
)
perm_registry.register_permission(
    key='security.domain.create',
    label=_('Add Domain'),
    module='Security',
    description=_('Can add new custom domains to the tenant'),
    # is_dangerous=True,
)
perm_registry.register_permission(
    key='security.domain.verify',
    label=_('Verify Domain'),
    module='Security',
    description=_('Can trigger DNS verification checks for domains'),
)
perm_registry.register_permission(
    key='security.domain.manage',
    label=_('Manage Domains'),
    module='Security',
    description=_('Can delete domains or change the primary domain'),
    # is_dangerous=True,
)
