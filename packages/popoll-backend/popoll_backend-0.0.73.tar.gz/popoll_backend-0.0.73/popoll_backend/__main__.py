#! /usr/bin/python3
import argparse
import sys
import flask
import json
import logging
import logging.handlers
import os

from flask_cors import CORS
from flask_restful import Api, Resource
from functools import wraps
from typing import Any

from popoll_backend.model.output.history import History
from popoll_backend.usecases.all.upload_polls import UploadPolls
from popoll_backend.usecases.poll.answer.create_answer import CreateAnswer
from popoll_backend.usecases.poll.date.create_date import CreateDate
from popoll_backend.usecases.poll.date.get_dates_user import GetDatesUser
from popoll_backend.usecases.poll.poll.create_poll import CreatePoll
from popoll_backend.usecases.poll.poll.delete_poll import DeletePoll
from popoll_backend.usecases.poll.user.create_user import CreateUser
from popoll_backend.usecases.poll.answer.delete_answer import DeleteAnswer
from popoll_backend.usecases.poll.date.delete_date import DeleteDate
from popoll_backend.usecases.all.delete_old_dates import DeleteOldDates
from popoll_backend.usecases.poll.user.delete_user import DeleteUser
from popoll_backend.usecases.poll.instrument.get_instruments_all import GetInstrumentsAll
from popoll_backend.usecases.all.get_all_sessions import GetAllSession
from popoll_backend.usecases.poll.answer.get_answer import GetAnswer
from popoll_backend.usecases.poll.date.get_date import GetDate
from popoll_backend.usecases.poll.date.get_date_details import GetDateDetails
from popoll_backend.usecases.poll.date.get_dates import GetDates
from popoll_backend.usecases.poll.instrument.get_instruments import GetInstruments
from popoll_backend.usecases.poll.poll.get_poll import GetPoll
from popoll_backend.usecases.poll.answer.get_answer_search import GetAnswerSearch
from popoll_backend.usecases.poll.session.get_session import GetSession
from popoll_backend.usecases.poll.user.get_user_with_instruments import GetUserWithInstruments
from popoll_backend.usecases.poll.user.get_users import GetUsers
from popoll_backend.usecases.poll.answer.update_answer import UpdateAnswer
from popoll_backend.usecases.poll.date.update_date import UpdateDate
from popoll_backend.usecases.poll.poll.update_poll import UpdatePoll
from popoll_backend.usecases.poll.session.create_session import CreateSession
from popoll_backend.usecases.poll.session.update_session import UpdateSession
from popoll_backend.usecases.poll.user.update_user import UpdateUser
from popoll_backend.utils import toJSON


app = flask.Flask(__name__)
CORS(app)
api = Api(app)


def body(request: flask.request, param: str, default: Any=None, mandatory=True):
    if request.data != None:
        _body = json.loads(request.data)
        return _body[param] if mandatory else _body.get(param, default)
    else:
        return flask.abort(400, f'Missing parameter [{param}]') if mandatory else default

def queryParam(request: flask.request, param: str) -> bool:
    return request.args.get(param, '') == 'true'

def history(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        _poll = kwargs.get('poll')
        res = f(*args, **kwargs)
        os.makedirs(os.path.join('.history', _poll), exist_ok=True)
        logger = logging.getLogger('my_logger')
        logger.handlers.clear()
        handler = logging.handlers.RotatingFileHandler(os.path.join('.history', _poll, f'{_poll}.history.log'), maxBytes=1073741824, backupCount=10)
        logger.addHandler(handler)
        logger.warning(toJSON(History(flask.request, res, kwargs)))
        return res
    return decorated





class PollPollEndpoint(Resource):
    def get(self, poll: str) -> str: return GetPoll(poll).run()
    
    @history
    def post(self, poll:str) -> str: return CreatePoll(poll, body(flask.request, 'name', mandatory=False, default=poll), body(flask.request, 'instruments', mandatory=False, default=[]), body(flask.request, 'color', mandatory=False, default="#000000")).run()
    
    @history
    def put(self, poll:str) -> str: return UpdatePoll(poll, body(flask.request, 'name'), body(flask.request, 'color')).run()
    
    @history
    def delete(self, poll: str) -> str: return DeletePoll(poll).run()
    
    
    

class PollInstrumentsEndpoint(Resource):
    def get(self, poll: str) -> str: 
        if queryParam(flask.request, 'used_only'):
            return GetInstruments(poll).run()
        else:
            return GetInstrumentsAll(poll).run()
    
    






class PollUsersEndpoint(Resource):
    def get(self, poll: str) -> str: return GetUsers(poll).run()
    
    @history
    def post(self, poll: str) -> str: return CreateUser(poll, body(flask.request, 'user')['name'], body(flask.request, 'main_instrument')['id'], [i['id'] for i in body(flask.request, 'instruments')]).run()



class PollUserEndpoint(Resource):
    def get(self, poll: str, id:int) -> str: 
        if queryParam(flask.request, 'details'):
            return GetDatesUser(poll, id).run()
        else:
            return GetUserWithInstruments(poll, id).run()
    
    @history
    def put(self, poll: str, id: int) -> str: return UpdateUser(poll, id, body(flask.request, 'user')['name'], body(flask.request, 'main_instrument')['id'], [i['id'] for i in body(flask.request, 'instruments')]).run()
    
    @history
    def delete(self, poll: str, id: int) -> str: return DeleteUser(poll, id).run()







class PollDatesEndpoint(Resource):
    def get(self, poll: str) -> str: return GetDates(poll).run()
    
    @history
    def post(self, poll: str) -> str: return CreateDate(
        poll, 
        body(flask.request, 'title'), 
        body(flask.request, 'date'), 
        body(flask.request, 'time', mandatory=False), 
        body(flask.request, 'end_time', mandatory=False),
        body(flask.request, 'is_frozen'), 
    ).run()



class PollDateEndpoint(Resource):
    def get(self, poll: str, id:int) -> str:
        if queryParam(flask.request, 'details'):
            return GetDateDetails(poll, id).run()
        else:
            return GetDate(poll, id).run()
    
    @history
    def put(self, poll: str, id: int) -> str: return UpdateDate(
        poll, 
        id, 
        body(flask.request, 'title'), 
        body(flask.request, 'date'), 
        body(flask.request, 'time', mandatory=False), 
        body(flask.request, 'end_time', mandatory=False),
        body(flask.request, 'is_frozen')
    ).run()
    
    @history
    def delete(self, poll: str, id: int) -> str: return DeleteDate(poll, id).run()







class PollAnswersEndpoint(Resource):
    
    @history
    def post(self, poll: str) -> str: return CreateAnswer(poll, body(flask.request, 'user_id'), body(flask.request, 'date_id')).run()


class PollAnswerEndpoint(Resource):
    
    def get(self, poll: str, id:int) -> str: return GetAnswer(poll, id).run()
    
    @history
    def put(self, poll: str, id: int) -> str: return UpdateAnswer(poll, id, body(flask.request, 'response')).run()
    
    @history
    def delete(self, poll: str, id: int) -> str: return DeleteAnswer(poll, id).run()

class PollGetAnswerEndpoint(Resource):
    def get(self, poll: str, userId: int, dateId: int) -> str: return GetAnswerSearch(poll, userId, dateId).run()





class PollSessionsEndpoint(Resource):
    @history
    def post(self, poll: str) -> str: return CreateSession(poll, body(flask.request, 'session_id'), body(flask.request, 'user_id')).run()


class PollSessionEndpoint(Resource):
    def get(self, poll: str, id: str) -> str: return GetSession(poll, id).run()
    
    @history
    def put(self, poll: str, id: str) -> str: return UpdateSession(poll, id, body(flask.request, 'user_id')).run()




class SessionEndpoint(Resource):
    def get(self, id: str) -> str: return GetAllSession(id).run()


class DatesEndpoint(Resource):
    def delete(self) -> str: return DeleteOldDates().run()
    
class PollsEndpoint(Resource):
    def post(self) -> str: return UploadPolls().run()


api.add_resource(SessionEndpoint, '/session/<string:id>')
api.add_resource(DatesEndpoint, '/date')
api.add_resource(PollsEndpoint, '/poll')

api.add_resource(PollPollEndpoint, '/<string:poll>')
api.add_resource(PollInstrumentsEndpoint, '/<string:poll>/instrument')
api.add_resource(PollUsersEndpoint, '/<string:poll>/user')
api.add_resource(PollUserEndpoint, '/<string:poll>/user/<int:id>')
api.add_resource(PollDatesEndpoint, '/<string:poll>/date')
api.add_resource(PollDateEndpoint, '/<string:poll>/date/<int:id>')
api.add_resource(PollAnswersEndpoint, '/<string:poll>/answer')
api.add_resource(PollAnswerEndpoint, '/<string:poll>/answer/<int:id>')
api.add_resource(PollGetAnswerEndpoint, '/<string:poll>/answer/<int:userId>/<int:dateId>')
api.add_resource(PollSessionsEndpoint, '/<string:poll>/session')
api.add_resource(PollSessionEndpoint, '/<string:poll>/session/<string:id>')


def get_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='the hostname to listen on', default='0.0.0.0')
    parser.add_argument('--port', help='the port of the webserver', default=4444)
    parser.add_argument('--debug', help='Enable debugging', action='store_true')
    return parser

def run(args):
    app.run(debug=args.debug, host=args.host, port=args.port)

if __name__ == '__main__':
    args = get_options().parse_args()
    run(args)
