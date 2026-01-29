import datetime

from popoll_backend.usecases.all.delete_old_dates import dateBefore
from tests import IntegrationTest

class TestDeleteOldDates(IntegrationTest):
    
    today = datetime.date.today()

    def setUp(self):
        super().setUp()
        self.date1_id = self.create_date(date=dateBefore(years=2).isoformat(), time='15:00:00', title='2yearsBefore', end_time=None)['id']
        self.date2_id = self.create_date(date=dateBefore(years=1, days=1).isoformat(), time='15:00:00', title='2yearsAnd1DayBefore', end_time=None)['id']
        self.date3_id = self.create_date(date=dateBefore(years=1).isoformat(), time='15:00:00', title='1yearBefore', end_time=None)['id']
        self.date4_id = self.create_date(date=dateBefore(years=1, days=-1).isoformat(), time='15:00:00', title='1yearMinus1DayBefore', end_time=None)['id']
        
    def test_getDaysBefore_method(self):
        self.assertEqual(datetime.date.today().isoformat(), dateBefore(years=0, days=0).isoformat())
        self.assertEqual("2023-05-29", dateBefore(datetime.date(2024, 5, 29), 1, 0).isoformat())
        self.assertEqual("2024-05-28", dateBefore(datetime.date(2024, 5, 29), 0, 1).isoformat())
        self.assertEqual("2023-05-28", dateBefore(datetime.date(2024, 5, 29), 1, 1).isoformat())
        self.assertEqual("2023-05-30", dateBefore(datetime.date(2024, 5, 29), 1, -1).isoformat())
        
        
    def test_delete_old_dates(self):
        self.delete_old_date()
        _json = self.get_dates()
        self.assertEqual(2, len(_json))
        