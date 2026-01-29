from popoll_backend.usecases.all.delete_old_dates import NEXT_DAY
from tests import IntegrationTest

class TestUpdateDate(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.date1_id = self.create_date(date=NEXT_DAY, time='15:00:00', title='firstDate', end_time='18:00:00')['id']
        
    def test_update_date(self):
        _json = self.udpate_date(self.date1_id, date=NEXT_DAY, title='firstDate', time=None, end_time=None)
        self.assertDate(_json, self.date1_id, NEXT_DAY, None, None, 'firstDate', False)
        _json = self.get_date(self.date1_id, False)
        self.assertDate(_json, self.date1_id, NEXT_DAY, None, None, 'firstDate', False, False)

    def test_update_freeze_date(self):
        _json = self.udpate_date(self.date1_id, date=NEXT_DAY, time='15:00:00', title='firstDate', end_time='18:00:00', is_frozen=True)
        self.assertTrue(_json['is_frozen'])
        
        self.user1_id = self.create_user('user1', self.instru2_id, [self.instru1_id])['user']['id']
        _rs = self.create_answer(self.user1_id, self.date1_id, fail=True)
        self.assertEqual(403, _rs.status_code)
        
        _json2 = self.get_date(self.date1_id, False)
        self.assertDate(_json2, self.date1_id, NEXT_DAY, '15:00:00', '18:00:00', 'firstDate', True, False)
        