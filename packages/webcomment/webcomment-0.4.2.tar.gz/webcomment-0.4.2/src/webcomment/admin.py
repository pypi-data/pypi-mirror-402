from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Comment,
    Reaction,
    Setting,
    Thread,
    ThreadTarget,
)


class TenantLinkMixin:
    def tenant_link(self, obj):
        if obj.tenant:
            url = reverse('admin:saas_base_tenant_change', args=[obj.tenant.id])
            return format_html('<a href="{}">{}</a>', url, obj.tenant)
        return '-'

    tenant_link.short_description = 'Tenant'


class ThreadLinkMixin:
    def thread_link(self, obj):
        if obj.thread:
            url = reverse('admin:webcomment_thread_change', args=[obj.thread.id])
            return format_html('<a href="{}">{}</a>', url, obj.thread)
        return '-'

    thread_link.short_description = 'Thread'


class PriceLinkMixin:
    def price_link(self, obj):
        if obj.price:
            url = reverse('admin:saas_stripe_price_change', args=[obj.price.id])
            return format_html('<a href="{}">{}</a>', url, obj.price)
        return '-'

    price_link.short_description = 'Price'


@admin.register(Setting)
class SettingAdmin(TenantLinkMixin, admin.ModelAdmin):
    list_display = ['tenant_link', 'allow_origin', 'allow_webmention', 'allow_anonymous', 'auto_close']


@admin.register(Thread)
class ThreadAdmin(TenantLinkMixin, admin.ModelAdmin):
    list_display = ['id', 'tenant_link', 'title', 'url', 'created_at']


@admin.register(ThreadTarget)
class ThreadTargetAdmin(ThreadLinkMixin, admin.ModelAdmin):
    list_display = ['id', 'thread_link', 'webmention_endpoint', 'target', 'status_code', 'published_at', 'created_at']


@admin.register(Comment)
class CommentAdmin(TenantLinkMixin, ThreadLinkMixin, admin.ModelAdmin):
    list_display = ['id', 'tenant_link', 'thread_link', 'type', 'status', 'reply_root', 'created_at']


@admin.register(Reaction)
class ReactionAdmin(TenantLinkMixin, ThreadLinkMixin, admin.ModelAdmin):
    list_display = ['id', 'tenant_link', 'thread_link', 'type', 'created_at']
