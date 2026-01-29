from saas_base.registry import perm_registry

perm_registry.register_scope(
    key='comment:read',
    label='Read Comments',
    permissions=['content.comment.view'],
    description='Read-only access to comments',
)

perm_registry.register_scope(
    key='comment:write',
    label='Manage Comments',
    permissions=['content.comment.manage'],
    description='Full write access to comments',
)

perm_registry.register_scope(
    key='comment:admin',
    label='Administer Comments',
    permissions=['content.comment.*'],
    description='Full control over comments',
)
