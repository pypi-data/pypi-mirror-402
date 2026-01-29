import requests

MF_PARSER_URL = 'https://node.microformats.io/'
WEBMENTION_TYPES = [
    'in-reply-to',
    'like-of',
    'repost-of',
    'bookmark-of',
]


def parse_received_webmention(source: str, target: str):
    for item in fetch_entries(source):
        author = parse_author(item)
        url = _flat_properties(item, 'url')
        published = _flat_properties(item, 'published')
        updated = _flat_properties(item, 'updated')
        data = {
            'url': url,
            'source': source,
            'author': author,
        }
        if published:
            data['published'] = published
        if updated:
            data['updated'] = updated

        for _type in WEBMENTION_TYPES:
            if target == parse_field_link(item, _type):
                if _type == 'in-reply-to':
                    yield {
                        'type': 'reply',
                        'name': _flat_properties(item, 'name'),
                        'content': _flat_properties(item, 'content'),
                        **data,
                    }
                else:
                    yield {
                        'type': _type.replace('-of', ''),
                        **data,
                    }


def parse_sending_targets(thread_url: str):
    urls = set([])
    for item in fetch_entries(thread_url):
        if thread_url == _flat_properties(item, 'url'):
            for _type in WEBMENTION_TYPES:
                link = parse_field_link(item, _type)
                if link:
                    urls.add(link)

    for target in urls:
        try:
            endpoint = fetch_webmention_endpoint(target)
            yield target, endpoint
        except requests.exceptions.RequestException:
            continue


def fetch_entries(source: str):
    resp = requests.get(MF_PARSER_URL, params={'url': source}, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    for item in data.get('items', []):
        if 'type' in item and 'properties' in item and 'h-entry' in item['type']:
            yield item['properties']


def fetch_webmention_endpoint(source: str):
    resp = requests.get(MF_PARSER_URL, params={'url': source}, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    if 'rels' not in data:
        return None
    return _flat_properties(data['rels'], 'webmention')


def parse_field_link(properties, field: str):
    data = _flat_properties(properties, field)
    if not data:
        return None

    if isinstance(data, str):
        return data

    if isinstance(data, dict) and 'properties' in data:
        return _flat_properties(data['properties'], 'url')


def parse_author(properties):
    author = _flat_properties(properties, 'author')
    if not author:
        return

    data = author['properties']
    name = _flat_properties(data, 'name')
    url = _flat_properties(data, 'url')
    photo = _flat_properties(data, 'photo')
    if isinstance(photo, str):
        picture = photo
    elif isinstance(photo, dict):
        picture = photo.get('value')
    else:
        picture = None
    return {
        'name': name,
        'url': url,
        'picture': picture,
    }


def _flat_properties(properties, key: str):
    if key not in properties:
        return None

    value = properties[key]
    if isinstance(value, list) and len(value) == 1:
        value = value[0]

    return value
