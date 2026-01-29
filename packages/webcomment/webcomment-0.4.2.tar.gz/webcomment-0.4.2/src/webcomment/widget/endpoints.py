from datetime import timedelta

from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework.exceptions import NotFound
from saas_base.drf.views import Endpoint
from saas_base.identity.models import Membership
from saas_base.ipware import get_client_ip
from saas_base.rules import check_rules

from ..models import Comment, Reaction, Setting, Thread
from ..serializers import ThreadSerializer
from ..settings import comment_settings
from .serializers import (
    CommentCreationSerializer,
    CommentDetailSerializer,
    CommentSerializer,
)

REACTION_TYPES_INT_STR = {i: s for i, s in Reaction.ReactionType.choices}
REACTION_TYPES_STR_INT = {s: i for i, s in Reaction.ReactionType.choices}


class BrowserEndpoint(Endpoint):
    permission_classes = []

    def options(self, request, *args, **kwargs):
        response = HttpResponse()
        return self.set_access_control_allow(response)

    @staticmethod
    def set_access_control_allow(response: HttpResponse):
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response


class ThreadItemEndpoint(BrowserEndpoint):
    serializer_class = ThreadSerializer

    @staticmethod
    def get_comment_count(thread_id: str):
        comment_count = Comment.objects.filter(thread_id=thread_id, status=Comment.CommentStatus.APPROVED).count()
        return {'comment_count': comment_count}

    @staticmethod
    def reset_reaction_counts():
        data = {}
        for k in REACTION_TYPES_INT_STR:
            key = REACTION_TYPES_INT_STR[k] + '_count'
            data[key] = 0
        return data

    @classmethod
    def get_reaction_counts(cls, thread_id: str):
        data = cls.reset_reaction_counts()
        queryset = Reaction.objects.filter(thread_id=thread_id)
        reactions = queryset.values_list('type').annotate(Count('id'))
        for k, count in reactions:
            key = REACTION_TYPES_INT_STR[k] + '_count'
            data[key] = count
        return data

    @staticmethod
    def get_tenant_members(tenant_id: int):
        members = Membership.objects.filter(tenant_id=tenant_id).values_list('user_id', flat=True).all()
        return {'members': list(members)}

    def resolve_thread(self, request, **kwargs):
        thread_id = kwargs['thread_id']
        return self.get_object_or_404(Thread.objects.all(), pk=thread_id)

    def get(self, request, *args, **kwargs):
        thread = self.resolve_thread(request, **kwargs)
        serializer: ThreadSerializer = self.get_serializer(thread)
        data = serializer.data
        # add tenant members
        data.update(self.get_tenant_members(thread.tenant_id))

        try:
            settings = Setting.objects.get_from_cache_by_pk(thread.tenant_id)
            data['allow_origin'] = settings.allow_origin
            data['allow_webmention'] = settings.allow_webmention
            data['allow_anonymous'] = settings.allow_anonymous
        except Setting.DoesNotExist:
            pass

        now = timezone.now()
        if now - thread.created_at > timedelta(seconds=60):
            # add comment count
            data.update(self.get_comment_count(thread.id))
            # add reaction counts
            data.update(self.get_reaction_counts(thread.id))
        else:
            data.update({'comment_count': 0})
            data.update(self.reset_reaction_counts())

        response = JsonResponse(data)
        return self.set_access_control_allow(response)


class ThreadResolveEndpoint(ThreadItemEndpoint):
    def resolve_thread(self, request, **kwargs):
        thread = comment_settings.THREAD_RESOLVER.resolve(request)
        if not thread:
            raise NotFound()
        return thread


class CommentsEndpoint(BrowserEndpoint):
    def get(self, request, *args, **kwargs):
        thread_id = kwargs['thread_id']
        root_id = request.query_params.get('root')
        cursor = request.query_params.get('next')
        queryset = Comment.objects.filter(thread_id=thread_id, status__gt=0)
        queryset = queryset.select_related('webmention', 'login_user')
        if root_id:
            queryset = queryset.filter(reply_root=root_id)
        if cursor:
            try:
                queryset = queryset.filter(id__gt=int(cursor))
            except (TypeError, ValueError):
                pass

        queryset = queryset.order_by('id').all()[:50]
        serializer = CommentDetailSerializer(queryset, many=True)
        response = JsonResponse(serializer.data, safe=False)
        return self.set_access_control_allow(response)

    def post(self, request, *args, **kwargs):
        self.prevent_duplicate_request(get_client_ip(request), 60)
        check_rules(comment_settings.COMMENT_SECURITY_RULES, request)
        thread_id = kwargs['thread_id']
        thread = self.get_object_or_404(Thread.objects.all(), pk=thread_id)
        context = {'thread': thread, 'request': request}
        serializer = CommentCreationSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        serializer = CommentSerializer(obj)
        response = JsonResponse(serializer.data, status=201)
        return self.set_access_control_allow(response)


class ReactionsEndpoint(BrowserEndpoint):
    def get(self, request, *args, **kwargs):
        thread_id = kwargs['thread_id']
        queryset = Reaction.objects.filter(thread_id=thread_id)

        _type = request.query_params.get('type')
        if _type and _type in REACTION_TYPES_STR_INT:
            queryset = queryset.filter(type=REACTION_TYPES_STR_INT[_type])

        cursor = request.query_params.get('next')
        if cursor:
            try:
                queryset = queryset.filter(id__gt=int(cursor))
            except (TypeError, ValueError):
                pass

        queryset = queryset.values('id', 'type', 'metadata').order_by('id')[:200]
        data = {s: [] for s in REACTION_TYPES_STR_INT}
        for item in queryset:
            metadata = item['metadata']
            metadata['id'] = item['id']
            data[REACTION_TYPES_INT_STR[item['type']]].append(metadata)

        response = JsonResponse(data)
        return self.set_access_control_allow(response)
