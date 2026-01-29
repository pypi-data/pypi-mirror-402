from tests import IntegrationTest

class TestUpdateUser(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.user1_id = self.create_user('user1', self.instru2_id, [self.instru3_id, self.instru1_id])['user']['id']
        
    def test_update_user(self):
        _json = self.update_user(self.user1_id, 'user1bis', self.instru3_id, [self.instru1_id, self.instru2_id])
        self.assertUserWithInstruments(_json, self.user1_id, 'user1bis', self.instru3_id, [self.instru1_id, self.instru2_id])

    def test_update_user_invalid(self):
        self.user2_id = self.create_user('user2', self.instru2_id, [self.instru3_id, self.instru1_id])['user']['id']
        _rs = self.update_user(self.user2_id, 'user1', self.instru3_id, [self.instru1_id, self.instru2_id], fail=True)
        self.assertEqual(409, _rs.status_code)