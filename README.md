## Setup
### Windows
#### Dependancy Installation:
- ``pip install -r requirements.txt``

If you have problems with windows dependancies handling, you can use pipwin package.

- ``pip install pipwin``
- ``pipwin install pyaudio``

### Linux/Mac
#### Dependancy Installation:
- ``sudo apt install -y portaudio19-dev``
- ``sudo apt install -y pyaudio``
- ``pip install -r requirements.txt``

## Running 
### Windows
Just run client.py (server.py). I recommend using this platform.

### Linux
You should have keyboard package isntalled as root. The client part (client.py) should be run as root. Server part (server.py) does not require this. 

## Usage
- Specify ip and port of the server you want to connect to
- Specify a nickname (should be overall unique)
- Type a room id or create new room
- Press ``ctrl+m`` to speak
- Type ``d`` in the terminal to disconnect from the server
- You will be able to see nicknames of all peers in the room in the terminal
- Current speakers are marked with ``*`` sign (e.g. {Alice, *Bob} -- Bob is speaking)

## Requirements
- Python 3
- PyAudio
- Keyboard
- Socket Module (standard library)
- Threading Module (standard library)
- uuid (standart library)
- sys (standart library)

## License
[MIT](https://choosealicense.com/licenses/mit/)
