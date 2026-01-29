from popoll_backend.usecases.all.delete_old_dates import NEXT_DAY
from tests import IntegrationTest

class TestGetDate(IntegrationTest):

    def setUp(self):
        super().setUp()
        self.user1_id = self.create_user('user1', self.instru2_id, [self.instru1_id])['user']['id']
        self.user2_id = self.create_user('user2', self.instru1_id, [self.instru2_id])['user']['id']
        self.user3_id = self.create_user('user3', self.instru1_id, [self.instru2_id])['user']['id']
        self.date1_id = self.create_date(date=NEXT_DAY, time='15:00:00', title='firstDate', end_time='18:00:00')['id']
        self.answer1_id = self.create_answer(user_id=self.user1_id, date_id=self.date1_id)['id']
        self.answer2_id = self.create_answer(user_id=self.user2_id, date_id=self.date1_id)['id']
        self.update_answer(self.answer2_id, False)
        
    def test_get_date(self):
        _json = self.get_date(self.date1_id, False)
        self.assertDate(_json, self.date1_id, NEXT_DAY, '15:00:00', '18:00:00', 'firstDate', False, False)
        self.assertEqual(None, _json.get('answers', None))

    def test_get_date_details(self):
        _json = self.get_date(self.date1_id, True)
        self.assertDate(_json['date'], self.date1_id, NEXT_DAY, '15:00:00', '18:00:00', 'firstDate', False, False)
        
        self.assertEqual(6, len(_json['answers']))
        
        answer0 = _json['answers'][0]
        self.assertAnswer(answer0['answer'], self.answer1_id, self.user1_id, self.date1_id, True)
        self.assertUser(answer0['user'], self.user1_id, 'user1')
        self.assertInstrument(answer0['instrument'], self.instru2_id, self.INSTRU2, self.INSTRU2_RANK)
        self.assertTrue(answer0['is_main_instrument'])
        
        answer1 = _json['answers'][1]
        self.assertAnswer(answer1['answer'], self.answer1_id, self.user1_id, self.date1_id, True)
        self.assertUser(answer1['user'], self.user1_id, 'user1')
        self.assertInstrument(answer1['instrument'], self.instru1_id, self.INSTRU1, self.INSTRU1_RANK)
        self.assertFalse(answer1['is_main_instrument'])
        
        answer2 = _json['answers'][2]
        self.assertAnswer(answer2['answer'], self.answer2_id, self.user2_id, self.date1_id, False)
        self.assertUser(answer2['user'], self.user2_id, 'user2')
        self.assertInstrument(answer2['instrument'], self.instru1_id, self.INSTRU1, self.INSTRU1_RANK)
        self.assertTrue(answer2['is_main_instrument'])
        
        answer3 = _json['answers'][3]
        self.assertAnswer(answer3['answer'], self.answer2_id, self.user2_id, self.date1_id, False)
        self.assertUser(answer3['user'], self.user2_id, 'user2')
        self.assertInstrument(answer3['instrument'], self.instru2_id, self.INSTRU2, self.INSTRU2_RANK)
        self.assertFalse(answer3['is_main_instrument'])
        
        answer4 = _json['answers'][4]
        self.assertIsNone(answer4['answer'])
        self.assertUser(answer4['user'], self.user3_id, 'user3')
        self.assertInstrument(answer4['instrument'], self.instru1_id, self.INSTRU1, self.INSTRU1_RANK)
        self.assertTrue(answer4['is_main_instrument'])
        
        answer5 = _json['answers'][5]
        self.assertIsNone(answer5['answer'])
        self.assertUser(answer5['user'], self.user3_id, 'user3')
        self.assertInstrument(answer5['instrument'], self.instru2_id, self.INSTRU2, self.INSTRU2_RANK)
        self.assertFalse(answer5['is_main_instrument'])