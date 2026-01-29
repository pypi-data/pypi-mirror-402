from tests import IntegrationTest

class TestDeleteDate(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.date1_id = self.create_date(date='2025-03-10', time='15:00:00', title='firstDate', end_time='18:00:00')['id']
        self.date2_id = self.create_date(date='2025-03-11', time='15:00:00', title='secondDate', end_time='18:00:00')['id']
        
    def test_delete_date(self):
        self.delete_date(self.date1_id)
        _json = self.get_dates()
        self.assertEqual(1, len(_json))
        
    def test_delete_date_collateral(self):
        self.user1_id = self.create_user('user1', self.instru1_id, [])['user']['id']
        self.answer1_id = self.create_answer(self.user1_id, self.date1_id)
        self.delete_date(self.date1_id)
        _rs = self.get_answer(self.answer1_id, fail=True)
        self.assertEqual(404, _rs.status_code)
        
    def test_delete_date_not_existing(self):
        self.delete_date(99)
        _json = self.get_dates()
        self.assertEqual(2, len(_json))