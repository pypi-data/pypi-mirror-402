from saas_base.test import SaasTestCase

from webcomment.models import Reaction


class TestResolveAPI(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID
    tenant_slug = 'demo-1'
    thread_link = 'https://example.com/hello'
    resolve_url = '/widget/threads/resolve'

    def test_resolve_thread_data(self):
        resp = self.client.get(
            self.resolve_url,
            data={'url': self.thread_link, 'tenant': self.tenant_slug},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'open')
        self.assertEqual(data['comment_count'], 2)

    def test_resolve_thread_data_failed(self):
        # case 1: missing tenant
        resp = self.client.get(
            self.resolve_url,
            data={'url': self.thread_link},
            format='json',
        )
        self.assertEqual(resp.status_code, 404)

        # case 2: missing url
        resp = self.client.get(
            self.resolve_url,
            data={'tenant': self.tenant_slug},
            format='json',
        )
        self.assertEqual(resp.status_code, 404)

        # case 3: can not find tenant
        resp = self.client.get(
            self.resolve_url,
            data={'url': self.thread_link, 'tenant': 'not-found'},
        )
        self.assertEqual(resp.status_code, 404)

        # case 4: missing title
        resp = self.client.get(
            self.resolve_url,
            data={'tenant': self.tenant_slug, 'url': 'https://example.com/missing-1'},
            format='json',
        )
        self.assertEqual(resp.status_code, 404)

    def test_resolve_create_thread_data(self):
        url = 'https://example.com/create-1'
        title = 'Create 1'
        resp = self.client.get(
            self.resolve_url,
            data={'tenant': self.tenant_slug, 'url': url, 'title': title},
        )
        self.assertEqual(resp.status_code, 200)


class TestCommentsAPI(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID
    thread_url = '/widget/threads/00000000-0000-0000-0002-00000000000a'

    def test_get_thread_data(self):
        resp = self.client.get(self.thread_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'open')
        self.assertEqual(data['comment_count'], 2)
        self.assertEqual(data['members'], [3])

    def test_get_comments(self):
        resp = self.client.get(self.thread_url + '/comments')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 3)
        comment = data[0]
        self.assertEqual(comment['status'], 'approved')

    def test_create_comment_without_parent(self):
        data = {'name': 'User', 'email': 'user@example.com', 'content': 'help me'}
        resp = self.client.post(self.thread_url + '/comments', data=data, format='json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['user']['name'], 'User')

    def test_create_comment_with_parent(self):
        payload = {
            'name': 'User',
            'email': 'user@example.com',
            'content': 'help me',
            'parent': 1,
        }
        resp = self.client.post(self.thread_url + '/comments', data=payload, format='json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['reply_path'], '1')

        payload['parent'] = data['id']
        resp = self.client.post(self.thread_url + '/comments', data=payload, format='json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['reply_path'], '1/4')


class TestReactionsAPI(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID
    thread_id = '00000000-0000-0000-0002-00000000000a'
    thread_url = f'/widget/threads/{thread_id}/reactions'

    def prepare_reactions(self, reaction_type: int, count: int = 10):
        for i in range(count):
            Reaction.objects.create(
                tenant_id=self.tenant_id,
                thread_id=self.thread_id,
                type=reaction_type,
                source_sha1=f'sha-{reaction_type}-{i}',
                metadata={'source': ''},
            )

    def test_get_empty_reactions(self):
        resp = self.client.get(self.thread_url, format='json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for key in data:
            self.assertEqual(len(data[key]), 0)

    def test_list_reactions(self):
        self.prepare_reactions(Reaction.ReactionType.LIKE, 20)
        self.prepare_reactions(Reaction.ReactionType.REPOST, 20)
        self.prepare_reactions(Reaction.ReactionType.BOOKMARK, 20)
        resp = self.client.get(self.thread_url, format='json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['like']), 20)
        self.assertEqual(len(data['repost']), 20)
        self.assertEqual(len(data['bookmark']), 20)

        resp = self.client.get(self.thread_url, data={'type': 'like'}, format='json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['like']), 20)
        self.assertEqual(len(data['repost']), 0)

        resp = self.client.get(self.thread_url, data={'next': '9999'}, format='json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['like']), 0)
        self.assertEqual(len(data['repost']), 0)
        self.assertEqual(len(data['bookmark']), 0)
