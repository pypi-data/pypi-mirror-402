from saas_base.test import SaasTestCase

from webcomment.models import Comment


class TestCommentsAPI(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID
    base_url = '/api/comments/'

    def test_list_comments(self):
        self.force_login()
        resp = self.client.get(self.base_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['count'], 3)

    def test_list_pending_comments(self):
        self.force_login()
        resp = self.client.get(self.base_url + '?status=pending')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['count'], 1)

    def test_list_approved_comments(self):
        self.force_login()
        resp = self.client.get(self.base_url + '?status=approved')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['count'], 2)

    def test_approve_comment(self):
        self.force_login()
        payload = {'status': 'approved'}
        resp = self.client.patch(self.base_url + '2/', data=payload, format='json')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(self.base_url + '?status=approved')
        data = resp.json()
        self.assertEqual(data['count'], 3)

    def test_set_invalid_comment_status(self):
        self.force_login()
        payload = {'status': 'invalid'}
        resp = self.client.patch(self.base_url + '2/', data=payload, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_delete_comment(self):
        self.force_login()
        resp = self.client.delete(self.base_url + '2/')
        self.assertEqual(resp.status_code, 204)
        resp = self.client.get(self.base_url)
        data = resp.json()
        self.assertEqual(data['count'], 2)

    def test_reply_comment(self):
        self.force_login()
        # Reply to comment 1
        payload = {'content': 'Backend Reply'}
        resp = self.client.post(self.base_url + '1/reply/', data=payload, format='json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['content'], 'Backend Reply')
        # reply_root is excluded from serializer, verify via DB

        # Verify database
        reply = Comment.objects.get(pk=data['id'])
        self.assertEqual(reply.reply_root_id, 1)
        self.assertEqual(reply.content, 'Backend Reply')
        self.assertEqual(reply.login_user_id, self.user_id)

        # Verify reply count on parent
        parent = Comment.objects.get(pk=1)
        self.assertEqual(parent.reply_count, 1)

    def test_reply_nested_comment(self):
        self.force_login()
        # First reply
        c1 = Comment.objects.create(
            tenant_id=self.tenant_id,
            thread_id='00000000-0000-0000-0002-00000000000a',
            content='Root',
            status=Comment.CommentStatus.APPROVED,
        )
        c2 = Comment.objects.create(
            tenant_id=self.tenant_id,
            thread_id='00000000-0000-0000-0002-00000000000a',
            content='Child',
            reply_root=c1,
            reply_path=str(c1.id),
            status=Comment.CommentStatus.APPROVED,
        )
        Comment.reset_reply_count(c1.id)
        c1.refresh_from_db()
        self.assertEqual(c1.reply_count, 1)

        # Reply to Child (c2) via API
        payload = {'content': 'Grandchild'}
        resp = self.client.post(self.base_url + f'{c2.id}/reply/', data=payload, format='json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()

        # Check hierarchy
        # reply_root should be c1 (the root), NOT c2
        # self.assertEqual(data["reply_root"], c1.id) # Excluded from serializer
        # reply_path should be "c1.id/c2.id"
        self.assertEqual(data['reply_path'], f'{c1.id}/{c2.id}')

        # Check count update on ROOT
        c1.refresh_from_db()
        self.assertEqual(c1.reply_count, 2)
