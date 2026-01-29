from tests import IntegrationTest

class TestGetAnswer(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.user1_id = self.create_user('user1', self.instru2_id, [self.instru1_id])['user']['id']
        self.date1_id = self.create_date(date='2025-03-10', time='15:00:00', title='firstDate', end_time='18:00:00')['id']
        self.answer1_id = self.create_answer(self.user1_id, self.date1_id)['id']
        
    def test_get_answer_answerId(self):
        _json = self.get_answer(self.answer1_id)
        self.assertAnswer(_json, self.answer1_id, self.user1_id, self.date1_id, True)
