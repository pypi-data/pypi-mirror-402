from django.test import TestCase


class TestWebmentionEndpoint(TestCase):
    fixtures = [
        'test_data.yaml',
    ]
    tenant_slug = 'demo-1'

    def test_use_get_method(self):
        resp = self.client.get(f'/s/{self.tenant_slug}/webmention')
        self.assertEqual(resp.status_code, 202)

    def test_use_post_method(self):
        resp = self.client.post(f'/s/{self.tenant_slug}/webmention')
        self.assertEqual(resp.status_code, 400)

    def test_use_valid_url(self):
        resp = self.client.post(
            f'/s/{self.tenant_slug}/webmention',
            data={
                'source': 'invalid',
                'target': 'invalid',
            },
        )
        self.assertEqual(resp.status_code, 400)

    def test_use_same_domain(self):
        source = 'https://example.com/hello'
        resp = self.client.post(
            f'/s/{self.tenant_slug}/webmention',
            data={
                'source': source,
                'target': source,
            },
        )
        self.assertEqual(resp.status_code, 400)

    def test_use_invalid_tenant(self):
        resp = self.client.post(
            '/s/not-found/webmention',
            data={
                'source': 'https://example.com/hello',
                'target': 'https://lepture.com/',
            },
        )
        self.assertEqual(resp.status_code, 404)

    def test_use_correct_data(self):
        resp = self.client.post(
            f'/s/{self.tenant_slug}/webmention',
            data={
                'source': 'https://example.com/hello',
                'target': 'https://lepture.com/',
            },
        )
        self.assertEqual(resp.status_code, 202)

        # trigger cache
        resp = self.client.post(
            f'/s/{self.tenant_slug}/webmention',
            data={
                'source': 'https://example.com/hello',
                'target': 'https://lepture.com/',
            },
        )
        self.assertEqual(resp.status_code, 202)
