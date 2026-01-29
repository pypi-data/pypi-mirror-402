from typing import List, Optional
from popoll_backend.db.model.answer import Answer
from popoll_backend.db.model.date import Date
from popoll_backend.db.model.instrument import Instrument
from popoll_backend.db.model.user import User
from popoll_backend.db.model.user_instruments import UserInstruments

def getUser(users: List[User], id: int) -> User:
    return [user for user in users if user.id == id][0]

def getInstrument(instruments: List[Instrument], id: int) -> Instrument:
    return [instrument for instrument in instruments if instrument.id == id][0]

def getMainInstrument(instruments: List[Instrument], user_instruments: List[UserInstruments], user: User) -> Instrument:
    return getInstrument(instruments, [user_instrument.instrument_id for user_instrument in user_instruments if user_instrument.user_id == user.id and user_instrument.is_main][0])

def getSecondInstruments(instruments: List[Instrument], user_instruments: List[UserInstruments], user: User) -> List[Instrument]:
    return [getInstrument(instruments, iid) for iid in [user_instrument.instrument_id for user_instrument in user_instruments if user_instrument.user_id == user.id and not user_instrument.is_main]]

def getAnswer(answers: List[Answer], user_id: int):
    res: List[Answer] = [answer for answer in answers if answer.user_id == user_id]
    if len(res) == 0:
        return None
    if len(res) > 1:
        print('WEIRD CASE')
    return res[0]

class _DateAnswer:
    
    def __init__(self, answer: Answer, user: User, instrument: Instrument, is_main_instrument: bool):
        self.answer = answer
        self.user = user
        self.instrument = instrument
        self.is_main_instrument = is_main_instrument

class DateDetails:
    def __init__(self, date: Date, answers: List[Answer], users: List[User], instruments: List[Instrument], user_instruments: List[UserInstruments]):
        self.date: Date = date
        self.answers: List[_DateAnswer] = []
        for user in users:
            answer = getAnswer(answers, user.id)
            self.answers.append(_DateAnswer(answer, user, getMainInstrument(instruments, user_instruments, user), True))
            for instru in getSecondInstruments(instruments, user_instruments, user):
                self.answers.append(_DateAnswer(answer, user, instru, False))
        