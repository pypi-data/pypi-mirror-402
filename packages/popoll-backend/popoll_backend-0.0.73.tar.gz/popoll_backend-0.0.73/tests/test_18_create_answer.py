from tests import IntegrationTest

class TestCreateAnswer(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.user1_id = self.create_user('user1', self.instru2_id, [self.instru1_id])['user']['id']
        self.date1_id = self.create_date(date='2025-03-10', time='15:00:00', title='firstDate', end_time='18:00:00')['id']
        
    def test_create_answer(self):
        _json = self.create_answer(self.user1_id, self.date1_id)
        self.assertAnswer(_json, 1, self.user1_id, self.date1_id, True)
        
    def test_create_answer_dupe_error(self):
        _json = self.create_answer(self.user1_id, self.date1_id)
        self.assertAnswer(_json, 1, self.user1_id, self.date1_id, True)
        _rs = self.create_answer(self.user1_id, self.date1_id, fail=True)
        self.assertEqual(409, _rs.status_code)

    def test_create_answer_error(self):
        _rs = self.create_answer(self.user1_id, 99, fail=True)
        self.assertEqual(400, _rs.status_code)