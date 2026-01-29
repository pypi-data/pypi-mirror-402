import hashlib

import requests
from django.db import IntegrityError
from django.utils import timezone

from webcomment.models import Comment, Reaction, Thread, ThreadTarget, Webmention
from webcomment.webmention.parser import parse_received_webmention, parse_sending_targets

REACTION_TYPES_STR_INT = {s: i for i, s in Reaction.ReactionType.choices}


def receive_webmention(tenant_id: int, source: str, target: str):
    thread = Thread.objects.get_from_cache_by_natural_key(tenant_id, target)
    for item in parse_received_webmention(source, target):
        url = item['url']
        source_sha1 = hashlib.sha1(url.encode('utf-8')).hexdigest()
        if item['type'] == 'reply':
            create_comment(thread, source_sha1, item)
        else:
            create_reaction(thread, source_sha1, item)


def create_comment(thread: Thread, source_sha1: str, metadata):
    content = metadata.pop('content')

    content_text = content['value']
    content_html = content['html']
    if 'name' in metadata and metadata['name'] == content_text:
        metadata.pop('name')

    if len(content_html) > 800:
        if len(content_text) > 400:
            content = content_text[:400]
            metadata['text_overflow'] = True
        else:
            content = content_text
    else:
        metadata['text_html'] = True
        content = content_html

    webmention = Webmention.objects.filter(thread_id=thread.id, source_sha1=source_sha1).first()
    if webmention:
        webmention.metadata = metadata
        webmention.save()

        comment = webmention.comment
        comment.content = content
        comment.save()
    else:
        comment = Comment.objects.create(
            tenant_id=thread.tenant_id,
            thread_id=thread.id,
            type=Comment.CommentType.WEBMENTION,
            status=Comment.CommentStatus.APPROVED,
            anonymous_user=metadata['author'],
            content=content,
        )
        Webmention.objects.create(
            comment=comment,
            thread=thread,
            source_url=metadata['url'],
            source_sha1=source_sha1,
            metadata=metadata,
        )


def create_reaction(thread: Thread, source_sha1: str, metadata):
    try:
        Reaction.objects.create(
            tenant_id=thread.tenant_id,
            thread_id=thread.id,
            source_sha1=source_sha1,
            type=REACTION_TYPES_STR_INT[metadata['type']],
            metadata=metadata,
        )
    except IntegrityError:
        pass


def send_webmention(thread_id: int):
    thread = Thread.objects.get_from_cache_by_pk(thread_id)
    items = parse_sending_targets(thread.url)
    for target, endpoint in items:
        if endpoint:
            resp = requests.post(endpoint, data={'target': thread.url, 'source': target}, timeout=5)
            ThreadTarget.objects.create(
                tenant_id=thread.tenant_id,
                thread_id=thread.id,
                target=target,
                webmention_endpoint=endpoint,
                status=resp.status_code,
                published_at=timezone.now(),
            )
