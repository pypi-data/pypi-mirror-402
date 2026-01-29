from django.conf import settings
from django.db import models
from django.utils import timezone

from .thread import Thread


class Reaction(models.Model):
    class ReactionType(models.IntegerChoices):
        LIKE = 1, 'like'
        REPOST = 2, 'repost'
        BOOKMARK = 3, 'bookmark'

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        settings.SAAS_TENANT_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='+',
    )
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, db_index=True)
    source_sha1 = models.CharField(max_length=42, db_index=True)
    type = models.SmallIntegerField(choices=ReactionType.choices)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [
            ['thread', 'source_sha1'],
        ]
        db_table = 'webcomment_reaction'
        ordering = ['-id']
