from saas_base.test import SaasTestCase


class TestUserTokensAPI(SaasTestCase):
    user_id = SaasTestCase.OWNER_USER_ID

    def test_list_user_sessions(self):
        self.force_login()
        resp = self.client.get('/api/user/sessions/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['count'], 1)
        self.assertTrue(data['results'][0]['current_session'])

    def test_retrieve_user_session(self):
        self.force_login()
        resp = self.client.get('/api/user/sessions/')
        data = resp.json()
        session_id = data['results'][0]['id']
        resp = self.client.get(f'/api/user/sessions/{session_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['current_session'])

        resp = self.client.delete(f'/api/user/sessions/{session_id}/')
        self.assertEqual(resp.status_code, 204)
