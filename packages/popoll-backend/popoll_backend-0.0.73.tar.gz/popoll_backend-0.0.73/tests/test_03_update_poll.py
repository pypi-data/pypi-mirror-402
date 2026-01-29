from tests import IntegrationTest

class TestUpdatePoll(IntegrationTest):

    def test_db_creation(self):
        _json = self.update_poll('TESTTESTTEST', '#88fb00')
        self.assertEqual('TESTTESTTEST', _json['name'])
        self.assertEqual('#88fb00', _json['color'])
        
        _json = self.get_poll()
        self.assertEqual('TESTTESTTEST', _json['name'])
        self.assertEqual('#88fb00', _json['color'])
