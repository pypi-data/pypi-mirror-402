from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from saas_base.drf.views import TenantEndpoint

from ..models import Thread
from ..serializers import ThreadDetailSerializer, ThreadSerializer


class ThreadListEndpoint(ListModelMixin, TenantEndpoint):
    serializer_class = ThreadDetailSerializer
    queryset = Thread.objects.prefetch_related('targets').all()
    required_permission = 'content.comment.view'

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ThreadStatusEndpoint(TenantEndpoint):
    serializer_class = ThreadSerializer
    queryset = Thread.objects.all()
    required_permission = 'content.comment.settings'

    def patch(self, request, *args, **kwargs):
        thread = self.get_object()
        status = request.data.get('status')
        serializer = self.get_serializer(thread, data={'status': status}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': status})
