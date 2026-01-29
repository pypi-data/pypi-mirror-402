import contextlib
import os
from tests import DB_NAME, IntegrationTest

class TestCreatePoll(IntegrationTest):
    
    DB_NAME_2 = 'test_integration_2'
    
    def test_db_creation(self):
        _json = self.get_instruments(False)
        
        self.assertEqual(self.instru1_id, _json[0]['id'])
        self.assertEqual(self.INSTRU1, _json[0]['name'])
        self.assertEqual(self.instru2_id, _json[1]['id'])
        self.assertEqual(self.INSTRU2, _json[1]['name'])
        self.assertEqual(self.instru3_id, _json[2]['id'])
        self.assertEqual(self.INSTRU3, _json[2]['name'])
        
    def test_can_create_another_db(self):
        _json = self.create_poll(self.DB_NAME_2, self.DB_NAME_2, '#ff8b00')
        self.assertEqual({}, _json)

    def test_no_duplicate_poll_id(self):
        rs = self.create_poll(DB_NAME, self.DB_NAME_2, '#ff8b00', fail=True)
        self.assertEqual(409, rs.status_code)
        
    def tearDown(self):
        self.tearDown_db(self.DB_NAME_2)