from tests import DB_NAME, IntegrationTest

class TestGetSession(IntegrationTest):
    
    DB_2 = 'test_integration_2'
    DB_3 = 'test_integration_3'
    
    SESSION = 'XXXXX'

    def setUp(self):
        super().setUp()
        self.user1_id: int = self.create_user('user1', self.instru1_id, [])['user']['id']
        self.create_session(self.SESSION, self.user1_id)
        
        self.create_poll(self.DB_2, self.DB_2, '#ff8b01')
        self.create_user('user1', self.instru1_id, [], db=self.DB_2)
        self.create_session(self.SESSION, self.user1_id, db=self.DB_2)
        
        self.create_poll(self.DB_3, self.DB_3, '#ff8b02')
        
    def test_get_all_session(self):
        _json = self.get_all_session(self.SESSION)
        self.assertEqual(2, len(_json))
        self.assertPoll(_json[0], DB_NAME, 'TESTTEST')
        self.assertPoll(_json[1], self.DB_2, self.DB_2)

    def tearDown(self):
        self.tearDown_db(self.DB_2)
        self.tearDown_db(self.DB_3)