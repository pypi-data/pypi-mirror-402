from django.core.cache import cache
from rest_framework import serializers
from saas_base.drf.serializers import ModelSerializer
from saas_base.ipware import get_client_ip

from ..models import Comment
from ..serializers import WebmentionSerializer
from ..signals import comment_created


class CommentSerializer(ModelSerializer):
    user = serializers.JSONField(read_only=True)

    class Meta:
        model = Comment
        exclude = [
            'tenant',
            'thread',
            'reply_root',
            'login_user',
            'anonymous_user',
            'receive_email',
        ]


class CommentDetailSerializer(CommentSerializer):
    webmention = WebmentionSerializer(read_only=True)


class CommentCreationSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    content = serializers.CharField(required=True)
    parent = serializers.IntegerField(required=False)
    receive_email = serializers.BooleanField(required=False)

    def validate_parent(self, value: int):
        try:
            obj = Comment.objects.get(pk=value)
            thread = self.context['thread']
            if obj.thread_id != thread.id:
                raise serializers.ValidationError('Invalid parent comment')
            return obj
        except Comment.DoesNotExist:
            raise serializers.ValidationError('Invalid parent comment')

    def create(self, validated_data):
        thread = self.context['thread']
        request = self.context['request']
        anonymous_user = {
            'name': validated_data['name'],
            'email': validated_data['email'],
        }
        parent: Comment = validated_data.get('parent', None)
        content = validated_data['content']
        kwargs = {
            'tenant_id': thread.tenant_id,
            'thread': thread,
            'anonymous_user': anonymous_user,
            'content': content,
            'receive_email': validated_data.get('receive_email', False),
            'status': calculate_comment_status(request, content),
        }

        if parent:
            if parent.reply_root_id:
                kwargs['reply_root_id'] = parent.reply_root_id
            else:
                kwargs['reply_root_id'] = parent.id
            kwargs['reply_path'] = '/'.join(parent.paths)

        obj = Comment.objects.create(**kwargs)
        if obj.reply_root_id and obj.status == obj.CommentStatus.APPROVED:
            Comment.reset_reply_count(obj.reply_root_id)

        comment_created.send(Comment, instance=obj, request=request)
        return obj


def calculate_comment_status(request, content: str):
    user_agent = request.headers.get('User-Agent')
    if not user_agent:
        return Comment.CommentStatus.PENDING

    if len(content) < 20 and content.isascii():
        # too short, maybe spam
        return Comment.CommentStatus.PENDING

    ip = get_client_ip(request)
    key = f'comment:ip:{ip}'
    if cache.get(key):
        # too frequent, maybe spam
        return Comment.CommentStatus.PENDING

    cache.set(key, '1', timeout=100)

    if 'Safari/' in user_agent or 'Firefox/' in user_agent:
        if 'http://' not in content and 'https://' not in content:
            return Comment.CommentStatus.APPROVED

    return Comment.CommentStatus.PENDING
