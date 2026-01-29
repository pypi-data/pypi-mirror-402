from django.tasks import task

from webcomment.settings import comment_settings
from webcomment.webmention.actions import (
    receive_webmention,
)
from webcomment.webmention.actions import (
    send_webmention as _send_webmention,
)


@task(queue_name=comment_settings.TASK_QUEUE_NAME)
def create_webmention(tenant_id: int, source: str, target: str):
    receive_webmention(tenant_id, source, target)


@task(queue_name=comment_settings.TASK_QUEUE_NAME)
def send_webmention(thread_id: int):
    _send_webmention(thread_id)
