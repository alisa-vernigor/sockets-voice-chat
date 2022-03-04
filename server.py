#!/usr/bin/python3

import socket
import threading
import logging
import events

class Server:
    def __init__(self):
        logging.basicConfig(level=logging.ERROR)
        self.ip = socket.gethostbyname(socket.gethostname())

        # nicknames support
        self.nicknames = set()
        self.clients_to_nicknames = dict()

        # speakers identifier

        # rooms support
        self.clients_to_room = dict()
        self.rooms_to_clients = dict()


        while 1:
            try:
                self.port = int(input('Enter port number to run on --> '))

                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.bind((self.ip, self.port))

                break
            except:
                print("Couldn't bind to that port")

        self.connections = []
        self.accept_connections()

    def accept_connections(self):
        self.s.listen(100)
    
        print('Running on IP: '+self.ip)
        print('Running on port: '+str(self.port))
        
        while True:
            c, addr = self.s.accept()
            logging.debug(f'Accepted new client, addr: {addr[0]}:{addr[1]}')

            # get clients nickname
            while True:
                nickname = c.recv(1024).decode('utf-8')
                logging.debug(f'Nickname {nickname}, len: {len(nickname)}')
                if nickname in self.nicknames:
                    c.send(bytes('0', 'utf-8'))
                else:
                    self.nicknames.add(nickname)
                    self.clients_to_nicknames[c] = nickname
                    c.send(bytes('1', 'utf-8'))
                    break
            
            # get clients room
            while True:
                inp = c.recv(1).decode('utf-8')
                room_id = c.recv(1024).decode('utf-8')


                if inp == '1':
                    if not room_id in self.rooms_to_clients:
                        c.send(b'1')
                        continue
                break


            self.clients_to_room[c] = room_id
            if not room_id in self.rooms_to_clients:
                self.rooms_to_clients[room_id] = set()
            self.rooms_to_clients[room_id].add(c)
            c.send(b'0')

            enc_cur_nick = self.clients_to_nicknames[c].encode('utf-8')

            # get clients in room
            for client in self.rooms_to_clients[self.clients_to_room[c]]:
                enc_nick = self.clients_to_nicknames[client].encode('utf-8')
                c.send(events.EventName.CONNECTED.to_bytes() + enc_nick + b' ' * (1023 - len(enc_nick)))

                if client != c:
                    client.send(events.EventName.CONNECTED.to_bytes() + enc_cur_nick + b' ' * (1023 - len(enc_cur_nick)))

            c.send(events.EventName.FIN_STREAM.to_bytes())

            self.connections.append(c)

            threading.Thread(target=self.handle_client,args=(c,addr,)).start()
        
    def broadcast(self, sock, recording):
        for client in self.rooms_to_clients[self.clients_to_room[sock]]:
            if client != self.s and client != sock:
                try:
                    data = events.EventName.VOICE.to_bytes() + recording
                    client.send(data)
                except:
                    pass

    def process_client_data(self, data, c):
        event = events.bytes_to_event(data[:1])
        
        if event == events.EventName.VOICE:
            recording = data[1:]
            self.broadcast(c, recording)
        elif event == events.EventName.START_SPEAKER:
            enc_nick = self.clients_to_nicknames[c].encode('utf-8')
            for peer in self.rooms_to_clients[self.clients_to_room[c]]:
                try:
                    peer.send(events.EventName.START_SPEAKER.to_bytes() + enc_nick + b' ' * (2048 - len(enc_nick)))
                except:
                    pass
        elif event == events.EventName.FIN_SPEAKER:
            enc_nick = self.clients_to_nicknames[c].encode('utf-8')
            for peer in self.rooms_to_clients[self.clients_to_room[c]]:
                try:
                    peer.send(events.EventName.FIN_SPEAKER.to_bytes() + enc_nick + b' ' * (2048 - len(enc_nick)))
                except:
                    pass

    def handle_client(self,c,addr):
        while 1:
            if not c in self.connections:
                break

            try:
                data = c.recv(2049)
                self.process_client_data(data, c)
            except Exception as e:
                if c in self.connections:
                    enc_nick = self.clients_to_nicknames[c].encode('utf-8')
                    for peer in self.rooms_to_clients[self.clients_to_room[c]]:
                        if peer != c:
                            try:
                                peer.send(events.EventName.DISCONNECTED.to_bytes() + enc_nick + b' ' * (2048 - len(enc_nick)))
                            except:
                                pass

                name = self.clients_to_nicknames.pop(c)
                self.nicknames.remove(name)
                self.connections.remove(c)
                self.rooms_to_clients[self.clients_to_room[c]].remove(c)
                self.clients_to_room.pop(c)
                try:
                    c.close()
                except:
                    pass
                break

server = Server()