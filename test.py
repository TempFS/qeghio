import numpy as np
import RelayRouter
#from RelayRouter import d
import Packet
import client
import channel
import random
from const import *
local_delay = 10




def test_client():

	p = []
	for i in range(1,6000):
		p.append(RelayRouter.RelayRouter(i, 200, random.choice(['A','B','C','D']), 1200, 0, ONLINE))
	'''
	r1 = RelayRouter.RelayRouter(1,200,'A', 1000, 0, ONLINE)
	r2 = RelayRouter.RelayRouter(2,200,'B', 1200, 0, ONLINE)
	r3 = RelayRouter.RelayRouter(3,200,'D', 1200, 0, ONLINE)
	r4 = RelayRouter.RelayRouter(4,200,'C', 1200, 0, ONLINE)
	r5 = RelayRouter.RelayRouter(5,200,'A', 1000, 0, ONLINE)
	r6 = RelayRouter.RelayRouter(6,200,'B', 1200, 0, ONLINE)
	r7 = RelayRouter.RelayRouter(7,200,'D', 1200, 0, ONLINE)
	r8 = RelayRouter.RelayRouter(8,200,'C', 1200, 0, ONLINE)
	r9 = RelayRouter.RelayRouter(9,200,'A', 1000, 0, ONLINE)
	r10 = RelayRouter.RelayRouter(10,200,'B', 1200, 0, ONLINE)
	r11 = RelayRouter.RelayRouter(11,200,'D', 1200, 0, ONLINE)
	r12 = RelayRouter.RelayRouter(12,200,'C', 1200, 0, ONLINE)
	'''
	RelayRouter.d.update_global_table()
	c1 = client.Client(10000,200, 'A', 0)
	c2 = client.Client(10001, 200, 'B', 0)
	RelayRouter.d.update_global_table()
	c1._entrynode = [1,4,5,6]
	c2._entrynode = [2,3]

	#RelayRouter.d.set_global_table([1,2,3,4,5,6,7,8,9,10,11,12])

	rrr = RelayRouter.RelayRouter(120,200,'C', 1200, 0, ONLINE)


	RelayRouter.d.update_global_table()
	channel.ch.load_delay('region_delay.txt')
	#p = [r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12]
	ct = get_current_time()
	while ct < 30000:
		channel.ch.handle()
		for _ in p:
			_.handle()
		c1.handle()
		c2.handle()
		if ct == 20:
			c1.send_to_server(1500, 10001)
			#c2.send_to_server(5000, 10000)

		add_a_timeslice()
		ct = get_current_time()



def test_channel():

	p1 = Packet.HandshakePacket(0, str(HANDSHAKE_COMMAND["RELAY_NOTE_FINDED"]) + '1')
	p1.set_from(2)
	p1.set_to(3)
	p2 = Packet.HandshakePacket(0, str(HANDSHAKE_COMMAND["RELAY_NOTE_FINDED"]) + '1')
	p2.set_from(2)
	p2.set_to(4)
	p3 = Packet.HandshakePacket(0, str(HANDSHAKE_COMMAND["RELAY_NOTE_FINDED"]) + '1')
	p3.set_from(1)
	p3.set_to(3)
	p4 = Packet.HandshakePacket(0, str(HANDSHAKE_COMMAND["RELAY_NOTE_FINDED"]) + '1')
	p4.set_from(4)
	p4.set_to(3)
	r1 = RelayRouter.RelayRouter(2,2,200,'A', 1000, 0, ONLINE)
	r2 = RelayRouter.RelayRouter(3,3,200,'B', 1200, 0, ONLINE)
	r3 = RelayRouter.RelayRouter(1,1,200,'D', 1200, 0, ONLINE)
	r4 = RelayRouter.RelayRouter(4,4,200,'C', 1200, 0, ONLINE)
	RelayRouter.d.update_global_table()
	ch.load_delay('region_delay.txt')
	p = [r1,r2,r3,r4]
	ct = get_current_time()
	while ct < 3000:
		ch.handle()
		for _ in p:
			_.handle()
		if ct == 20:
			ch.SendPacket(p1)
		if ct == 30:
			ch.SendPacket(p2)
		if ct == 53:
			ch.SendPacket(p3)
		if ct == 610:
			ch.SendPacket(p4)

		add_a_timeslice()
		ct = get_current_time()




if __name__ == '__main__':
	test_client()


