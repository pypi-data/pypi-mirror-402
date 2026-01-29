from saas_base.test import SaasTestCase

from saas_auth.models import UserToken


class TestTokenAuthentication(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID
    tenant_id = 0

    def setup_user_token(self, scope):
        token = UserToken.objects.create(
            name='Test',
            scope=scope,
            user_id=self.user_id,
        )
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token.key)

    def test_can_not_fetch_tokens(self):
        self.setup_user_token('user')
        resp = self.client.get('/api/user/tokens/')
        self.assertEqual(resp.status_code, 403)

    def test_without_token(self):
        resp = self.client.get('/api/user/sessions/')
        self.assertEqual(resp.status_code, 403)

    def test_with_invalid_scope(self):
        self.setup_user_token('tenant')
        resp = self.client.get('/api/user/sessions/')
        self.assertEqual(resp.status_code, 403)

    def test_with_valid_scope(self):
        self.setup_user_token('user:read')
        resp = self.client.get('/api/user/sessions/')
        self.assertEqual(resp.status_code, 200)
