from const import *
import copy
class Packet():
	def __init__(self):
		self._length = 0
		self._seq = 0
		self._from = 0
		self._to = 0
		self._route_table = []
		self._fixed_route_table = []
		self._init_time = 0
		self._final_receiver = None
		self.resend_flag = False

 	def set_resend_flag(self):
		self.resend_flag = True

 	def set_final_receiver(self, final_receiver):
 		self._final_receiver = final_receiver

 	# This function cannot be called by Relay Routers
 	def get_final_receiver(self):
 		return self._final_receiver

	def set_fixed_route_table(self, table):
		self._fixed_route_table = table
		self._route_table = table[1:]

	def get_fixed_route_table(self):
		return copy.deepcopy(self._fixed_route_table)

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
			if len(self._route_table) == 0:
				return 0
			return self._route_table[0]

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
		return "seq:[%d], from:[%d], to:[%d]" % (self._seq, self._from, self._to)




class PayloadPacket(Packet):
	def __init__(self, packet_id, packet_sequence, packet_total):
		Packet.__init__(self)
		self._packet_id = packet_id
		self._packet_sequence = packet_sequence
		self._packet_total = packet_total
		self.set_length(TOR_PACKET_LENGTH)

	def get_packet_id(self):
		return self._packet_id

	def get_packet_sequence(self):
		return self._packet_sequence

	def get_packet_total(self):
		return self._packet_total
	def __str__(self):
		return "[PayloadPacket] packet_id:[%s], packet_sequence:[%d] " %(self._packet_id, self._packet_sequence) + Packet.__str__(self)




class ACKPacket(Packet):
	def __init__(self, seq, fr, to):
		self.set_seq(seq)
		self.set_from(fr)
		self.set_to(to)
		self.set_length(10)
		self.time_require = 0
	def __str__(self):
		return "[ACKPacket] "+ Packet.__str__(self) 


class HandshakePacket(Packet):
	def __init__(self, circuit_id, payload):
		Packet.__init__(self)
		self._circuit_id = circuit_id
		self._payload = payload
		self.set_length(512)
		self.note_table = []
		self.fast_note = []
	def set_note_table(self, n_t):
		self.note_table = copy.deepcopy(n_t)

	def set_fast_note_table(self, f_n_t):
		self.fast_note = copy.deepcopy(f_n_t)

	def get_note_table(self):
		return copy.deepcopy(self.note_table)

	def get_fast_note_table(self):
		return copy.deepcopy(self.fast_note)

	def get_payload(self):
		return self._payload

	def get_circuit_id(self):
		return self._circuit_id


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





