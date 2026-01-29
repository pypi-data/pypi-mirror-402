import datetime

from tests import IntegrationTest

class TestGetUser(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.user1_id = self.create_user('user1', self.instru2_id, [self.instru3_id, self.instru1_id])['user']['id']
        
    def test_get_user(self):
        _json = self.get_user(self.user1_id, False)
        self.assertUserWithInstruments(_json, self.user1_id, 'user1', self.instru2_id, [self.instru1_id, self.instru3_id])

    def test_get_user_details(self):
        self.date1_id = self.create_date(date='2028-03-10', time='15:00:00', title='firstDate', end_time='18:00:00')['id']
        self.date2_id = self.create_date(date='2022-03-10', time='15:00:00', title='oldDate', end_time='18:00:00')['id']
        self.answer1_id = self.create_answer(user_id=self.user1_id, date_id=self.date1_id)['id']
        _json = self.get_user(self.user1_id, True)
        self.assertUser(_json['user'], self.user1_id, 'user1')
        self.assertEqual(2, len(_json['dates']))
        self.assertDate(_json['dates'][0]['date'], self.date2_id, '2022-03-10', '15:00:00', '18:00:00', 'oldDate', False, True)
        self.assertDate(_json['dates'][1]['date'], self.date1_id, '2028-03-10', '15:00:00', '18:00:00', 'firstDate', False, False)
        self.assertAnswer(_json['dates'][1]['answer'], self.answer1_id, self.user1_id, self.date1_id, True)
        
    def test_get_user_details_with_old_dates(self):
        self.date1_id = self.create_date(date='2028-03-10', time='15:00:00', title='firstDate', end_time='18:00:00')['id']
        self.date2_id = self.create_date(date='2022-03-10', time='15:00:00', title='oldDate', end_time='18:00:00')['id']
        self.answer1_id = self.create_answer(user_id=self.user1_id, date_id=self.date1_id)['id']
        _json = self.get_user(self.user1_id, True)
        self.assertEqual(2, len(_json['dates']))
        
    def test_get_user_details_with_yesterday_and_today(self):
        today = datetime.date.today().strftime('%Y-%m-%d')
        yesterday = (datetime.datetime.now() - datetime.timedelta(1)).strftime('%Y-%m-%d')
        before_yesterday = (datetime.datetime.now() - datetime.timedelta(2)).strftime('%Y-%m-%d')
        self.date_today_with_time = self.create_date(date=today, time='15:00:00', title='today', end_time='18:00:00')['id']
        self.date_yesterday_with_time = self.create_date(date=yesterday, time='15:00:00', title='today', end_time='18:00:00')['id']
        self.date_before_yesterday_with_time = self.create_date(date=before_yesterday, time='15:00:00', title='today', end_time='18:00:00')['id']
        self.date_today_without_time = self.create_date(date=today, time=None, title='today', end_time=None)['id']
        self.date_yesterday_without_time = self.create_date(date=yesterday, time=None, title='today', end_time=None)['id']
        self.date_before_yesterday_without_time = self.create_date(date=before_yesterday, time=None, title='today', end_time=None)['id']
        _json = self.get_user(self.user1_id, True)
        self.assertEqual(6, len(_json['dates']))
        self.assertEqual(4, len([date for date in _json['dates'] if date['date']['is_old']]))
        