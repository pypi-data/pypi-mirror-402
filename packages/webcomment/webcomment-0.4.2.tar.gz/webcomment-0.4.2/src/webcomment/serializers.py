from rest_framework import serializers
from saas_base.drf.serializers import ModelSerializer

from .models import Comment, Reaction, Setting, Thread, ThreadTarget, Webmention
from .signals import comment_created


class SettingSerializer(ModelSerializer):
    class Meta:
        model = Setting
        exclude = ['tenant']


class ThreadSerializer(ModelSerializer):
    id = serializers.UUIDField(format='hex', read_only=True)

    class Meta:
        model = Thread
        exclude = ['tenant']


class ThreadTargetSerializer(ModelSerializer):
    class Meta:
        model = ThreadTarget
        exclude = ['tenant', 'thread']


class ThreadDetailSerializer(ThreadSerializer):
    targets = ThreadTargetSerializer(many=True, read_only=True)


class WebmentionSerializer(ModelSerializer):
    class Meta:
        model = Webmention
        fields = ['source_url', 'metadata']


class ReactionSerializer(ModelSerializer):
    thread = ThreadSerializer(read_only=True)

    class Meta:
        model = Reaction
        exclude = ['tenant', 'source_sha1']


class CommentSerializer(ModelSerializer):
    thread = ThreadSerializer(read_only=True)
    user = serializers.JSONField(read_only=True)
    webmention = WebmentionSerializer(read_only=True, required=False)

    class Meta:
        model = Comment
        exclude = [
            'tenant',
            'reply_root',
            'login_user',
            'anonymous_user',
            'receive_email',
        ]


class CommentReplySerializer(serializers.Serializer):
    content = serializers.CharField(required=True)

    def create(self, validated_data):
        parent: Comment = self.context['parent']
        request = self.context['request']
        user = self.context['user']
        content = validated_data['content']
        kwargs = {
            'tenant_id': parent.tenant_id,
            'thread_id': parent.thread_id,
            'login_user': user,
            'anonymous_user': {},
            'content': content,
            'receive_email': False,
            'status': Comment.CommentStatus.APPROVED,
        }
        if parent.reply_root_id:
            kwargs['reply_root_id'] = parent.reply_root_id
        else:
            kwargs['reply_root_id'] = parent.id
        kwargs['reply_path'] = '/'.join(parent.paths)
        obj = Comment.objects.create(**kwargs)
        Comment.reset_reply_count(obj.reply_root_id)
        comment_created.send(Comment, instance=obj, request=request)
        return obj
