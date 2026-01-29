from django.dispatch import receiver

from webcomment.registry import default_roles, default_scopes  # noqa
from webcomment.signals import thread_created, webmention_received
from webcomment.tasks import create_webmention, send_webmention


@receiver(webmention_received)
def on_webmention_received(sender, **kwargs):
    create_webmention.enqueue(
        tenant_id=kwargs['tenant_id'],
        source=kwargs['source'],
        target=kwargs['target'],
    )


@receiver(thread_created)
def on_thread_created(sender, instance, **kwargs):
    send_webmention.enqueue(str(instance.id))
