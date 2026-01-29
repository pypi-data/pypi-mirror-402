from tests import IntegrationTest

class TestGetSearchAnswer(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.user1_id = self.create_user('user1', self.instru2_id, [self.instru1_id])['user']['id']
        self.date1_id = self.create_date(date='2025-03-10', time='15:00:00', title='firstDate', end_time='18:00:00')['id']
        self.answer1_id = self.create_answer(self.user1_id, self.date1_id)['id']
        
    def test_get_search_answer_userId_dateId(self):
        _json = self.get_search_answer(self.user1_id, self.date1_id)
        self.assertAnswer(_json, self.answer1_id, self.user1_id, self.date1_id, True)
        
    def test_get_search_answer_userId_dateId_notFound(self):
        _rs = self.get_search_answer(99, self.date1_id, fail=True)
        self.assertEqual(404, _rs.status_code)
