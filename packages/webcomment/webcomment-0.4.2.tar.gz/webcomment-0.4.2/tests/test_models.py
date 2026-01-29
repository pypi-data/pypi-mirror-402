from saas_base.test import SaasTestCase

from webcomment.models import Comment


class TestModels(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID

    def test_comment_user_property(self):
        # Coverage for Comment.user property
        c = Comment.objects.get(pk=1)
        # It has no login_user or anonymous_user in fixture
        self.assertEqual(c.user, {})

        # Assign login_user
        c.login_user_id = self.user_id
        c.save()
        user_info = c.user
        self.assertEqual(user_info['id'], self.user_id)

        # Assign anonymous_user
        c.login_user = None
        c.anonymous_user = {'name': 'Anon', 'email': 'a@b.com'}
        c.save()
        user_info = c.user
        self.assertEqual(user_info['name'], 'Anon')
        self.assertTrue('picture' in user_info)
