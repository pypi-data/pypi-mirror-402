from popoll_backend.usecases.all.delete_old_dates import NEXT_DAY, dateAfter, dateBefore
from tests import IntegrationTest

class TestGetDates(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.date1_id = self.create_date(date=dateBefore(days=2).isoformat(), time='15:00:00', title='firstDate', end_time=None)['id']
        self.date2_id = self.create_date(date=dateAfter(days=2).isoformat(), time=None, end_time=None, title='secondDate')['id']
        self.date3_id = self.create_date(date=NEXT_DAY, time='15:00:00', title='thirdDate', end_time='18:00:00')['id']
        self.date4_id = self.create_date(date=NEXT_DAY, title='fourthDate', end_time='18:00:00', time=None)['id']
        
    def test_get_dates(self):
        _json = self.get_dates()
        self.assertEqual(4, len(_json))
        self.assertDates(_json, 0, self.date1_id, dateBefore(days=2).isoformat(), '15:00:00', None, 'firstDate', False, True)
        self.assertDates(_json, 1, self.date4_id, NEXT_DAY, None, '18:00:00', 'fourthDate', False, False)
        self.assertDates(_json, 2, self.date3_id, NEXT_DAY, '15:00:00', '18:00:00', 'thirdDate', False, False)
        self.assertDates(_json, 3, self.date2_id, dateAfter(days=2).isoformat(), None, None, 'secondDate', False, False)
