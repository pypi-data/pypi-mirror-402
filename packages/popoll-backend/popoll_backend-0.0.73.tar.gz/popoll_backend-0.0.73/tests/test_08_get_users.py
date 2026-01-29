from tests import IntegrationTest

class TestGetUsers(IntegrationTest):

    def setUp(self):
        super().setUp()
        
    def test_get_users_sorted(self):
        self.create_user('user2', self.instru1_id, [])
        self.create_user('user1', self.instru1_id, [])
        _json = self.get_users()
        self.assertEqual(2, len(_json))
        self.assertUsers(_json, 0, 2, 'user1')
        self.assertUsers(_json, 1, 1, 'user2')

    def test_get_users_case(self):
        self.create_user('user1', self.instru1_id, [])
        self.create_user('User2', self.instru1_id, [])
        self.create_user('user3', self.instru1_id, [])
        _json = self.get_users()
        self.assertEqual(3, len(_json))
        self.assertUsers(_json, 0, 1, 'user1')
        self.assertUsers(_json, 1, 2, 'User2')
        self.assertUsers(_json, 2, 3, 'user3')
