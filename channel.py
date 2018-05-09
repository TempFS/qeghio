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
				if _elm[2] == 'No':
					_elm[2] = 100
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
		if 'ACKPacket' not in str(pkg):
			pass
			#print str(current_time) + str(pkg)
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
	pkg.resend_flag = False
	ch.SendPacket(pkg)
	
def global_resend(pkg):
	pkg.resend_flag = True
	ch.SendPacket(pkg)
