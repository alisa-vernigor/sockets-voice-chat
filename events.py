from enum import Enum

class EventName(Enum):
    VOICE = 1
    CONNECTED = 2
    DISCONNECTED = 3   
    FIN_SPEAKER = 4
    FIN_STREAM = 5
    START_SPEAKER = 6

    def to_bytes(self):
        return bytes(str(self.value), 'utf-8')

def bytes_to_event(data):
    try:
        ret = EventName(int(data.decode('utf-8')))
    except:
        ret = EventName.VOICE
    return ret

