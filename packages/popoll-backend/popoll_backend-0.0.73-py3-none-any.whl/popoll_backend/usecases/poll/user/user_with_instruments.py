from typing import List
from popoll_backend.db.model.user import User
from popoll_backend.db.model.instrument import Instrument
from popoll_backend.db.model.user_instruments import UserInstruments


class UserWithInstruments:
    
    def __init__(self, user: User, instruments: List[Instrument], user_instruments: List[UserInstruments]):
        self.user = user
        self.main_instrument: Instrument = self.getInstrument(instruments, self.getInstrumentIds(user_instruments, user.id, True)[0])
        self.instruments: List[Instrument] = self.getInstruments(instruments, self.getInstrumentIds(user_instruments, user.id, False))
        
    def getInstrumentIds(self, user_instruments: List[UserInstruments], user_id: int, is_main: bool):
        return [user_instrument.instrument_id for user_instrument in user_instruments if user_instrument.user_id == user_id and user_instrument.is_main == is_main]
    
    def getInstruments(self, instruments: List[Instrument], ids: List[int]):
        return [instrument for instrument in instruments if instrument.id in ids]
    
    def getInstrument(self, instruments: List[Instrument], id: int):
        return [instrument for instrument in instruments if instrument.id == id][0]