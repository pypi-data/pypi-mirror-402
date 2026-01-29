from tests import IntegrationTest

class TestGetSession(IntegrationTest):
    
    SESSION = 'XXXXX'

    def setUp(self):
        super().setUp()
        
    def test_create_session_noUser(self):
        _rs = self.create_session(self.SESSION, 1, fail=True)
        self.assertEqual(400, _rs.status_code)
        
    def test_create_session(self):
        self.user1_id = self.create_user('user1', self.instru1_id, [])['user']['id']
        _json = self.create_session(self.SESSION, self.user1_id)
        self.assertSession(_json, self.SESSION, self.user1_id)
        