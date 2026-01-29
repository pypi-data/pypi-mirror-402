from tests import IntegrationTest

class TestDeleteUser(IntegrationTest):
    
    SESSION = 'XXXX'

    def setUp(self):
        super().setUp()
        self.user1_id = self.create_user('user1', self.instru1_id, [])['user']['id']
        self.user2_id = self.create_user('user2', self.instru1_id, [])['user']['id']
        
    def test_delete_user(self):
        _json = self.delete_user(self.user1_id)
        self.assertEqual({}, _json)

    def test_delete_user_invalid(self):
        _rs = self.delete_user(99, fail=True)
        self.assertEqual(200, _rs.status_code)
        self.assertEqual({}, _rs.json)
        
    def test_delete_user_check_session(self):
        self.create_session(self.SESSION, self.user1_id)
        self.assertSession(self.get_session(self.SESSION), self.SESSION, self.user1_id)
        self.delete_user(self.user1_id)
        _rs = self.get_session(self.SESSION, fail=True)
        self.assertEqual(404, _rs.status_code)