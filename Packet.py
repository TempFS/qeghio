from const import *
class Packet():
	def __init__(self):
		self._length = 0
		self._seq = 0
		self._from = 0
		self._to = 0
		self._route_table = []
		self._fixed_route_table = []
		self._init_time = 0

	def set_fixed_route_table(self, table):
		self._fixed_route_table = table
		self._route_table = table[1:]

	def get_fixed_route_table(self):
		return self._fixed_route_table

	def set_init_time(self, init_time):
		self._init_time = init_time

	def get_init_time(self):
		return self._init_time

	def get_next_route(self):
		if len(self._route_table) == 0:
			return 0
		else:
			tmp = self._route_table[0]
			del self._route_table[0]
			return tmp

	def set_length(self, length):
		self._length = length
	def get_length(self):
		return self._length
	def set_seq(self, seq):
		self._seq = seq
	def get_seq(self):
		return self._seq
	def set_from(self, fr):
		self._from = fr
	def get_from(self):
		return self._from
	def set_to(self, to):
		self._to = to
	def get_to(self):
		return self._to
	def __str__(self):
		return "seq:[%x], from:[%x], to:[%x]" % (self._seq, self._from, self._to)




class PayloadPacket(Packet):
	def __init__(self, packet_id, packet_sequence):
		Packet.__init__(self)
		self._packet_id = packet_id
		self._packet_sequence = packet_sequence
		self.set_length(TOR_PACKET_LENGTH)

	def __str__(self):
		return "[PayloadPacket] packet_id:[%d], packet_sequence:[%d] " %(self._packet_id, self._packet_sequence) + Packet.__str__(self)




class ACKPacket(Packet):
	def __init__(self, seq, fr, to):
		self.set_seq(seq)
		self.set_from(fr)
		self.set_to(to)
		self.set_length(10)
	def __str__(self):
		return "[ACKPacket] "+ Packet.__str__(self) 


class HandshakePacket(Packet):
	def __init__(self, circuit_id, payload):
		Packet.__init__(self)
		self._circuit_id = circuit_id
		self._payload = payload
		self.set_length(512)

	def get_payload(self):
		return self._payload


class Payload():
	def __init__(self, payload_id, length):
		self._length = length
		self._id = payload_id

	def partition(self):
		payload_packet_list = []
		total_length = self._length
		seq = 0
		while total_length > 0:
			p = PayloadPacket(self._id, seq)
			seq += 1
			total_length -= TOR_PACKET_LENGTH
			payload_packet_list.append(p)
		return payload_packet_list



def packet_test():
	p = Payload(1, 4312)
	p_list = p.partition()
	seq = 0
	for _ in p_list:
		_.set_to(0x13133)
		_.set_from(0x77442)
		_.set_seq(seq)
		print _

if __name__ == '__main__':
	packet_test()




