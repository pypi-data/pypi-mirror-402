from rest_framework.response import Response
from saas_base.drf.views import TenantEndpoint

from ..models import Setting
from ..serializers import SettingSerializer


class SettingEndpoint(TenantEndpoint):
    serializer_class = SettingSerializer
    required_permission = 'content.comment.settings'

    def get_object(self):
        tenant_id = self.get_tenant_id()
        try:
            obj = Setting.objects.get_from_cache_by_pk(tenant_id)
        except Setting.DoesNotExist:
            obj = Setting.objects.create(tenant_id=tenant_id)

        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        setting = self.get_object()
        serializer = self.get_serializer(setting)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        setting = self.get_object()
        serializer = self.get_serializer(setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
