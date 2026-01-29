from tests import IntegrationTest

class TestCreateUser(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.create_user('user1', self.instru1_id, [])
        self.create_user('user3', self.instru2_id, [])
        
    def test_create_user_conflict(self):
        _json = self.get_users()
        self.assertEqual(2, len(_json))
        _rs = self.create_user('user1', self.instru1_id, [], fail=True)
        self.assertEqual(409, _rs.status_code)
        
    def test_create_user_conflict_case_insensitive(self):
        _json = self.get_users()
        self.assertEqual(2, len(_json))
        _rs = self.create_user('User1', self.instru1_id, [], fail=True)
        self.assertEqual(409, _rs.status_code)

    def test_create_user_valid(self):
        # Pre-check
        _json = self.get_users()
        self.assertEqual(2, len(_json))
        
        # Create user
        _json = self.create_user('user2', self.instru2_id, [self.instru3_id])
        self.assertEqual(3, _json['user']['id'])
        self.assertEqual('user2', _json['user']['name'])
        self.assertInstrument(_json['main_instrument'], self.instru2_id, self.INSTRU2, self.INSTRU2_RANK)
        self.assertEqual(1, len(_json['instruments']))
        self.assertInstruments(_json['instruments'], 0, self.instru3_id, self.INSTRU3, self.INSTRU3_RANK)
        
        # Post check
        _json = self.get_users()
        self.assertEqual(3, len(_json))
        self.assertUsers(_json, 0, 1, 'user1')
        self.assertUsers(_json, 1, 3, 'user2')
        self.assertUsers(_json, 2, 2, 'user3')
        
    def test_create_user_dupe_instrument(self):
        user4_id = self.create_user('user4', self.instru1_id, [self.instru1_id])['user']['id']
        self.assertEqual(0, len(self.get_user(user4_id, False)['instruments']))
        
    def test_create_user_not_existing_instrument(self):
        _rs = self.create_user('user4', 99, [], fail=True)
        self.assertEqual(400, _rs.status_code)