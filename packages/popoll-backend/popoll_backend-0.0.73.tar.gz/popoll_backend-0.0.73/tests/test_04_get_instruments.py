from tests import IntegrationTest

class TestGetInstruments(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.user1_id = self.create_user('user1', self.instru1_id, [self.instru2_id])['user']['id']
        self.user2_id = self.create_user('user2', self.instru2_id, [self.instru1_id])['user']['id']

    def test_get_instruments(self):
        _json = self.get_instruments(False)
        self.assertEqual(9, len(_json))
        self.assertTrue(self.INSTRU1 in [i['name'] for i in _json])
        self.assertTrue(self.INSTRU2 in [i['name'] for i in _json])
        self.assertTrue(self.INSTRU3 in [i['name'] for i in _json])
        
    def test_get_instruments_used_only(self):
        _json = self.get_instruments(True)
        self.assertEqual(2, len(_json))
        self.assertTrue(self.INSTRU1 in [i['name'] for i in _json])
        self.assertTrue(self.INSTRU2 in [i['name'] for i in _json])
        
    def test_get_instruments_used_only_all_used(self):
        self.update_user(self.user2_id, 'user2', self.instru2_id, [self.instru1_id, self.instru3_id])
        _json = self.get_instruments(True)
        self.assertEqual(3, len(_json))

