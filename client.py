#!/usr/bin/python3

import socket
import threading
import pyaudio
import sys
import keyboard
import uuid
import events

class Client:
    def __init__(self):
        self._stop_event = threading.Event()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.is_pressed = False

        self.clients_in_room = set()
        self.room_lock = threading.Lock()

        self.last_output_len = 0

        while 1:
            try:
                self.target_ip = input('Enter IP address of server --> ')
                self.target_port = int(input('Enter target port of server --> '))

                self.s.connect((self.target_ip, self.target_port))

                print('Connection established.')

                # get clients nickname
                while True:
                    self.nickname = input('Enter Nickname --> ')
                    if self.nickname == '':
                        print('ERROR: empty nickname not allowed, try again.')
                        continue

                    self.s.send(bytes(self.nickname, 'utf-8'))
                    data = self.s.recv(1)

                    if data == b'1':
                        print('You have successfully registered.')
                        break
                    else:
                        print('ERROR: This nickname is already in use. Please try again with another nickname.')
                
                # get clients room
                while True:
                    idr = input('Enter a room ID to connect to an existing room, or leave it blank to create a new one --> ')

                    if idr == '':
                        self.s.send(b'0')
                        idr = str(uuid.uuid4())
                    else:
                        self.s.send(b'1')

                    self.s.send(bytes(idr, 'utf-8'))

                    ans = self.s.recv(1).decode('utf-8')

                    if ans == '0':
                        print(f'Connected to the room: {idr}')
                        self.room = idr
                        break
                    else:
                        print(f'No such room: {idr}, try again.')

                # get other client in the room
                while True:
                    data = self.s.recv(1024)
                    event = events.bytes_to_event(data[:1])

                    if event == events.EventName.FIN_STREAM:
                        break
                    else:
                        nickname = data[1:].decode('utf-8').rstrip()
                        self.clients_in_room.add(nickname)

                break
            except:
                print("Couldn't connect to server")

        chunk_size = 1023 # 512
        audio_format = pyaudio.paInt16
        channels = 1
        rate = 20000

        # initialise microphone recording
        self.p = pyaudio.PyAudio()
        self.playing_stream = self.p.open(format=audio_format, channels=channels, rate=rate, output=True, frames_per_buffer=chunk_size)
        self.recording_stream = self.p.open(format=audio_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk_size)
        

        print("Connected to Server\n")
        self.output_clients()

        # start threads
        self.receive_thread = threading.Thread(target=self.receive_server_data).start()
     #   self.clients_in_room_thread = threading.Thread(target=self.output_clients).start()
        self.send_thread = threading.Thread(target=self.send_data_to_server).start()
        self.client_input_thread = threading.Thread(target=self.handle_client_input).start()

    def receive_server_data(self):
        while True:
            if self._stop_event.is_set():
                break
            try:
                data = self.s.recv(2049)
                self.process_server_data(data)
            except:
                pass

    def output_clients(self):       
        with self.room_lock:
            out = str(self.clients_in_room)
            if len(out) < self.last_output_len:
                out += ' ' * (self.last_output_len - len(out))
            sys.stdout.write(f'\r{out}')
            sys.stdout.flush()
            self.last_output_len = len(out)

    def process_server_data(self, data):
        event = events.bytes_to_event(data[:1])
        
        if event == events.EventName.VOICE:
            recording = data[1:]
            self.playing_stream.write(recording)
        elif event == events.EventName.DISCONNECTED:
            nickname = data[1:].decode('utf-8').rstrip()
            with self.room_lock:
                self.clients_in_room.remove(nickname)
            self.output_clients()
        elif event == events.EventName.CONNECTED:
            nickname = data[1:].decode('utf-8').rstrip()
            with self.room_lock:
                self.clients_in_room.add(nickname)
            self.output_clients()
        elif event == events.EventName.START_SPEAKER:
            nickname = data[1:].decode('utf-8').rstrip()
            with self.room_lock:
                self.clients_in_room.remove(nickname)
                self.clients_in_room.add('*' + nickname)
            self.output_clients()
        elif event == events.EventName.FIN_SPEAKER:
            nickname = data[1:].decode('utf-8').rstrip()
            with self.room_lock:
                self.clients_in_room.remove('*' + nickname)
                self.clients_in_room.add(nickname)
            self.output_clients()
    def handle_client_input(self):
        while True:
            command = sys.stdin.readline().rstrip()

            if command == 'd':
                self.s.close()
                self._stop_event.set()
                print('disconnected')
                break
            else:
                print('Unknown command, type \'help\' to see all available commands.')


    def send_data_to_server(self):
        while True:
            if self._stop_event.is_set():
                break
            try:
                if keyboard.is_pressed('ctrl+m'):
                    if not self.is_pressed:
                        self.s.sendall(events.EventName.START_SPEAKER.to_bytes() + b' ' * 2048)
                    recording = self.recording_stream.read(1024)
                    data = events.EventName.VOICE.to_bytes() + recording
                    self.s.sendall(data)
                    self.is_pressed = True
                else:
                    if self.is_pressed:
                        self.s.sendall(events.EventName.FIN_SPEAKER.to_bytes() + b' ' * 2048)
                    self.is_pressed = False
            except Exception as e:
                print(e)
                pass


client = Client()