from django.core.cache import cache
from django.http import HttpResponse
from saas_base.models import get_tenant_model

from webcomment.models import Webmention
from webcomment.signals import webmention_received

TenantModel = get_tenant_model()


def receive_webmention(request, slug):
    if request.method != 'POST':
        return HttpResponse(b'Method not allowed', status=202)

    schemes = ('https://', 'http://')
    source = request.POST.get('source', '')
    target = request.POST.get('target', '')
    if source.startswith(schemes) and target.startswith(schemes):
        if source != target:
            key = f'webmention.received:{slug}|{source}|{target}'
            if not cache.get(key):
                try:
                    tenant = TenantModel.objects.get_by_slug(slug)
                except TenantModel.DoesNotExist:
                    return HttpResponse(b'not found', status=404)

                webmention_received.send(
                    Webmention,
                    tenant_id=tenant.id,
                    source=source,
                    target=target,
                    request=request,
                )
                # save in 1 day
                cache.set(key, '1', timeout=86400)
            return HttpResponse(status=202)
    return HttpResponse(b'Invalid request', status=400)
