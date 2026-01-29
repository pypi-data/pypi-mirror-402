from popoll_backend.usecases.all.delete_old_dates import NEXT_DAY
from tests import IntegrationTest

class TestCreateDate(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.date1_id = self.create_date(date=NEXT_DAY, time='15:00:00', end_time=None, title='firstDate')['id']
        
    def test_create_date(self):
        self.assertEqual(1, len(self.get_dates()))
        self.date2_id = self.create_date(date=NEXT_DAY, title='secondDate', time=None, end_time=None)['id']
        _json = self.get_dates()
        self.assertEqual(2, len(_json))
        self.assertDates(_json, 0, self.date2_id, NEXT_DAY, None, None, 'secondDate', False, False)
        
    def test_create_date_only_end_time(self):
        self.assertEqual(1, len(self.get_dates()))
        self.date2_id = self.create_date(date=NEXT_DAY, title='secondDate', time=None, end_time='18:00:00')['id']
        _json = self.get_dates()
        self.assertEqual(2, len(_json))
        self.assertDates(_json, 0, self.date2_id, NEXT_DAY, None, '18:00:00', 'secondDate', False, False)
