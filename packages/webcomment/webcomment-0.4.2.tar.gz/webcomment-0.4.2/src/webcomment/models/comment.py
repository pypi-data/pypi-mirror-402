from django.conf import settings
from django.db import models
from django.utils import timezone
from saas_base.identity.gravatar import gen_gravatar_url

from .thread import Thread


class Comment(models.Model):
    class CommentType(models.IntegerChoices):
        COMMENT = 1, 'comment'
        WEBMENTION = 2, 'webmention'

    class CommentStatus(models.IntegerChoices):
        HIDDEN = 0, 'hidden'
        PENDING = 1, 'pending'
        APPROVED = 2, 'approved'

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        settings.SAAS_TENANT_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='+',
    )
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, db_index=True)
    type = models.SmallIntegerField(choices=CommentType.choices, default=CommentType.COMMENT)
    status = models.SmallIntegerField(choices=CommentStatus.choices, default=CommentStatus.PENDING)

    reply_root = models.ForeignKey(
        'Comment',
        on_delete=models.SET_NULL,
        db_index=True,
        related_name='+',
        null=True,
        blank=True,
    )
    reply_path = models.TextField(editable=False, null=True, blank=True)
    reply_count = models.IntegerField(default=0)

    login_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    anonymous_user = models.JSONField(blank=True, null=True)
    receive_email = models.BooleanField(default=False)

    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-id']
        db_table = 'webcomment_comment'
        indexes = [
            models.Index(fields=['thread', 'status']),
        ]

    @property
    def paths(self):
        if self.reply_path:
            return self.reply_path.split('/') + [str(self.id)]
        return [str(self.id)]

    @property
    def user(self):
        rv = {}
        if self.login_user_id:
            email = self.login_user.email
            rv['id'] = self.login_user_id
            rv['name'] = self.login_user.get_full_name()
        elif self.anonymous_user:
            email = self.anonymous_user.get('email')
            rv['name'] = self.anonymous_user.get('name')
        else:
            return {}

        if self.anonymous_user and 'picture' in self.anonymous_user:
            rv['picture'] = self.anonymous_user['picture']
        elif email:
            name = rv.get('name')
            rv['picture'] = gen_gravatar_url(email, name)
        return rv

    @classmethod
    def reset_reply_count(cls, comment_id: int):
        count = cls.objects.filter(reply_root=comment_id, status=cls.CommentStatus.APPROVED).count()
        cls.objects.filter(pk=comment_id).update(reply_count=count)


class Webmention(models.Model):
    comment = models.OneToOneField(Comment, on_delete=models.CASCADE, primary_key=True)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, db_index=True)
    source_url = models.URLField(max_length=255)
    source_sha1 = models.CharField(max_length=42, null=True, blank=True, db_index=True)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = [
            ['thread', 'source_sha1'],
        ]
        db_table = 'webcomment_webmention'
