from rest_framework.exceptions import ParseError
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from saas_base.drf.views import TenantEndpoint

from ..models import Comment
from ..serializers import CommentReplySerializer, CommentSerializer
from ..signals import comment_updated


class CommentListEndpoint(ListModelMixin, TenantEndpoint):
    serializer_class = CommentSerializer
    queryset = Comment.objects.select_related('thread', 'webmention', 'login_user')
    required_permission = 'content.comment.view'

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status')
        status_choices = {s: i for i, s in Comment.CommentStatus.choices}
        if status and status in status_choices:
            queryset = queryset.filter(status=status_choices[status])
        return queryset.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class CommentItemEndpoint(TenantEndpoint):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    required_permission = 'content.comment.manage'

    def patch(self, request: Request, *args, **kwargs):
        comment = self.get_object()
        status = request.data.get('status')
        status_choices = {s: i for i, s in Comment.CommentStatus.choices}
        if status and status in status_choices:
            comment.status = status_choices[status]
            comment.save()
            comment_updated.send(sender=self.__class__, instance=comment, status=status)
            return Response({'status': status})
        else:
            raise ParseError()

    def delete(self, request: Request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        return Response(status=204)


class CommentReplyEndpoint(TenantEndpoint):
    serializer_class = CommentReplySerializer
    queryset = Comment.objects.all()
    required_permission = 'content.comment.manage'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        context['parent'] = self.get_object()
        return context

    def post(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return Response(data=CommentSerializer(instance=obj).data, status=201)
