import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from saas_base.db import CachedManager


class ThreadManager(CachedManager['Thread']):
    cache_ttl = 86400
    query_select_related = ['tenant']
    natural_key = ['tenant_id', 'url']


class Thread(models.Model):
    class CommentStatus(models.IntegerChoices):
        DISABLED = -1, 'disabled'
        CLOSED = 0, 'closed'
        OPEN = 1, 'open'

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    tenant = models.ForeignKey(
        settings.SAAS_TENANT_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='+',
    )
    title = models.CharField(max_length=480)
    url = models.URLField(max_length=255)
    status = models.SmallIntegerField(choices=CommentStatus.choices, default=CommentStatus.OPEN)
    created_at = models.DateTimeField(default=timezone.now)
    objects = ThreadManager()

    def __str__(self):
        return f'Thread <{self.url}>'

    class Meta:
        ordering = ['-created_at']
        db_table = 'webcomment_thread'
        unique_together = [
            ('tenant', 'url'),
        ]


class ThreadTarget(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        settings.SAAS_TENANT_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='+',
    )
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='targets',
    )
    webmention_endpoint = models.URLField(max_length=255)
    target = models.URLField(max_length=255)
    status_code = models.SmallIntegerField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        db_table = 'webcomment_thread_target'
