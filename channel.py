import numpy as np
import RelayRouter
#from RelayRouter import d
import bisect
import Packet
from const import *
local_delay = 10




class Channel():
	def __init__(self):
		self.delay_table = {}
		self.send_list = []

	def load_delay(self, delay_file):
		fp = open(delay_file, 'r')
		lines = fp.readlines()
		self.delay_table = {}
		for line in lines:
			_elm = line.split()
			if len(_elm) != 3 or _elm[0] == _elm[1]:
				logging.error("Dealy table file format error.")
				continue
			x = _elm[0]
			y = _elm[1]
			if x < y:
				if x not in self.delay_table:
					self.delay_table[x] = {}
					self.delay_table[x][x] = local_delay
				self.delay_table[x][y] = float(_elm[2])
				if y not in self.delay_table:
					self.delay_table[y] = {}
					self.delay_table[y][y] = local_delay
				self.delay_table[y][x] = float(_elm[2])

	def get_avg_delay(self, regionA, regionB):
		if regionA < regionB:
			A = regionA
			B = regionB
		else:
			A = regionB
			B = regionA
		if self.delay_table.has_key(A):
			if self.delay_table[A].has_key(B):
				avg = self.delay_table[A][B]
			else:
				return -1
		else:
			return -1
		'''
		sigma = 0.6
		np.random.seed()
		s = np.random.normal(avg, sigma, 1)
		'''
		return avg

	def SendPacket(self, pkg):
		current_time = get_current_time()
		print str(current_time) + str(pkg)
		source = RelayRouter.d.get_router_object_by_id(pkg.get_from())
		destination = RelayRouter.d.get_router_object_by_id(pkg.get_to())
		delay = self.get_avg_delay(source.region, destination.region)
		send_item = {}
		send_item['sent_time'] = current_time + delay
		send_item['pkg'] = pkg
		self.send_list.append(send_item)
		self.send_list.sort(key=lambda r:r["sent_time"])


	def send_success(self, pkg):
		source = RelayRouter.d.get_router_object_by_id(pkg.get_from())
		destination = RelayRouter.d.get_router_object_by_id(pkg.get_to())
		destination.recv(source, pkg)


	def handle(self):
		current_time = get_current_time()
		size = len(self.send_list)
		i = 0
		while self.send_list:
			if self.send_list[i]["sent_time"] < current_time:
				self.send_success(self.send_list[i]["pkg"])
				del self.send_list[i]
				continue
			else:
				break

ch = Channel()
def global_send(pkg):  # src is the source object; dst is the destination ip!!!!
	ch.SendPacket(pkg)
	

def test():

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
	test()



