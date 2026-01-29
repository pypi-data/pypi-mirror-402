from saas_base.registry import perm_registry

perm_registry.assign_to_role('ADMIN', 'content.comment.*')
perm_registry.assign_to_role('MEMBER', 'content.comment.view')
