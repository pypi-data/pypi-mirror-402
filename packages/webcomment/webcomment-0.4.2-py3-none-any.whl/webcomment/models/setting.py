from django.conf import settings
from django.db import models
from saas_base.db import CachedManager


class SettingManager(CachedManager['Setting']):
    cache_ttl = 86400
    query_select_related = ['tenant']


class Setting(models.Model):
    tenant = models.OneToOneField(
        settings.SAAS_TENANT_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='+',
    )
    allow_origin = models.CharField(max_length=255, default='*')
    allow_webmention = models.BooleanField(default=False)
    allow_anonymous = models.BooleanField(default=True)
    auto_close = models.IntegerField(default=0)  # auto close thread comment after n days
    objects = SettingManager()

    class Meta:
        db_table = 'webcomment_setting'
