from abc import ABCMeta, abstractmethod
from typing import Optional

from rest_framework.request import Request
from saas_base.models import get_tenant_model

from webcomment.models import Thread
from webcomment.signals import thread_created

TenantModel = get_tenant_model()


class BaseResolver(object, metaclass=ABCMeta):
    def __init__(self, **options):
        self.options = options

    @abstractmethod
    def resolve(self, request: Request) -> Optional[Thread]: ...


class ModelThreadResolver(BaseResolver):
    @staticmethod
    def create_thread(tenant: TenantModel, request: Request) -> Optional[Thread]:
        title = request.query_params.get('title')
        url = request.query_params.get('url')
        if not title:
            return None

        thread = Thread.objects.create(
            tenant=tenant,
            url=url,
            title=title,
        )
        thread_created.send(Thread, instance=thread, request=request)
        return thread

    def resolve(self, request: Request) -> Optional[Thread]:
        slug = request.query_params.get('tenant')
        url = request.query_params.get('url')
        if not slug or not url:
            return None

        try:
            tenant = TenantModel.objects.get_by_slug(slug)
        except TenantModel.DoesNotExist:
            return None

        try:
            return Thread.objects.get_from_cache_by_natural_key(tenant.id, url)
        except Thread.DoesNotExist:
            return self.create_thread(tenant, request)
