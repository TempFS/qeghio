from channel import global_send, current_time
import random
import Packet
import RelayRouter
import copy
from const import *
global_entry_node = []  #store the id of entry node (the first node).


def fs(s):
	x = random.random()
	return 1.0 * (pow(2, s*x) - 1) / (pow(2,x) - 1)

class Circuit():
	def __init__(self, id, route_table, dest, n):
		self.route_table = route_table
		#self.n = len(self.route_table)
		self.id = id
		self.dest = dest
		self.n = n
	def set_route_table(self, r_t):
		self.route_table = r_t
		#self.n = len(self.route_table)
	def get_route_table(self):
		return copy.deepcopy(self.route_table)


class Client():
	def __init__(self, id, bandwidth, location, s):   # s: parameter
		self.id = id
		self._ip = id
		self._bandwidth = bandwidth
		self.region = location
		self._entrynode = []
		self.s = s
		self._route_time = 3  #luyou cishu, default:3
		self._probability = 1.0   #probability to choose a random router point

		self._ack_waited_list = {}						# a list recording the seq of packets that have not received ack.
		self._ack_buffer = []								# a buffer to reveive ack packet
		self.seq = 0
		self._buffer = []
		self._buffer_used = 0

		self._next_trans_time = 0
		self._current_circuit_count = 0
		self._circuit_map = {}			#{circuit_index : circuit id}
		self._establishing_circuit = {}    #{circuit_id : destiniton ip address}
		self._established_circuit = {}		#{destinition ip address : circuit_id}

		self._rend_circuit = {}
		self._send_content = {}   #{circuit_index : send_payload}
		self.current_handle = None
		RelayRouter.d._client_table[id] = self
		self._relay_node_table = []
		self.refresh_relay_node_table()

		self._packet_id = 0
		self._recv_buffer = {}    #{payload_packet_id : [packet1, packet2, packet3, ... ]

		self.resend_max_interval = 500
		self.resend_max_times = 3
	def refresh_relay_node_table(self):
		g_t = RelayRouter.d.get_global_table()
		for _ in g_t:
			self._relay_node_table.append(g_t[_])
		random.shuffle(self._relay_node_table)



	def refresh_entry_node_table(self):
		self._entrynode = global_entry_node

	def get_entry_node(self):
		index = int(fs(self.s) * len(self._entrynode))
		return self._entrynode[index]

	def get_relay_node(self, relay_node_table):
		if len(relay_node_table) <= 5:
			relay_node_table = self._relay_node_table
		#index = int(fs(self.s) * len(relay_node_table))
		index = random.randint(0, len(relay_node_table)-1)
		return relay_node_table[index]

	def get_a_rend_node(self):
		return random.choice(self._relay_node_table)

	def send_find_a_relay_note_packet(self, relay_note, circuit_id):
		pkt = Packet.HandshakePacket(circuit_id, str(HANDSHAKE_COMMAND["FIND_A_RELAY_NOTE"]) + str(self.id))
		pkt.set_fixed_route_table(relay_note)
		self.send(relay_note[1], pkt)

	def send_a_establish_rendezvous_packet(self, relay_note, circuit_id):
		pkt = Packet.HandshakePacket(circuit_id, str(HANDSHAKE_COMMAND["ESTABLISH_RENDEZVOUS"]) + str(circuit_id))
		pkt.set_fixed_route_table(relay_note)
		self.send(relay_note[1], pkt)


	def send_rend_inform_packet(self, server_id, rend_node_id, circuit_id):
		server = RelayRouter.d.get_router_object_by_id(server_id)
		server.recv_rand_inform_packet(self.id, rend_node_id, circuit_id)

	def recv_rand_inform_packet(self, client_id, rend_node_id, circuit_id):
		current_id = circuit_id.split(':')[0] + ':' + str(client_id)
		self.new_a_circuit(current_id, rend_node_id, 2)


 	#status True: First step to create a circuit_id
	def new_a_circuit(self, current_id, target_router_id, n): 
		# First step to create a circuit
		if len(self._entrynode) == 0:
			logging.error('Client has no known entry node')
			return -1

		relay_note = []
		relay_note.append(self.id)
		entry_node = self.get_entry_node()
		relay_note.append(entry_node)
		new_circuit = Circuit(current_id, relay_note, target_router_id, n)
		self._circuit_map[current_id] = new_circuit
		self._establishing_circuit[current_id] = new_circuit

		self.send_find_a_relay_note_packet(relay_note, current_id)


	def extend_a_circuit(self, current_circuit):
		router_table = self.current_handle.get_fixed_route_table()
		finished_n = len(router_table) - 1   # established relay notes
		if finished_n == current_circuit.n:
			# send to the destination

			router_table.reverse()
			router_table.append(current_circuit.dest)
			self.send_a_establish_rendezvous_packet(router_table, current_circuit.id)
		else:
			# continue find a relay router to extend the circuit
			note_table = self.current_handle.get_note_table()
			print router_table
			next_relay_id = self.get_relay_node(note_table)
			while next_relay_id.id in router_table or next_relay_id.id == current_circuit.dest:
				next_relay_id = self.get_relay_node(note_table)
			router_table.reverse()
			router_table.append(next_relay_id.id)
			self.send_find_a_relay_note_packet(router_table, current_circuit.id)

		
	def rendezvous_established(self):
		payload = self.current_handle.get_payload()
		flag = int(payload[1])
		circuit_id = self.current_handle.get_circuit_id()
		server_id = int(circuit_id.split(':')[1])
		route_table = self.current_handle.get_fixed_route_table()
		route_table.reverse()
		if flag == 1:
			self._rend_circuit[circuit_id] = route_table
			print server_id, circuit_id, route_table
			print 'rend ok.'



	def parse_handshake_packet(self):
		payload = self.current_handle.get_payload()
		cmd_flag = int(payload[0])
		if cmd_flag == HANDSHAKE_COMMAND["RELAY_NOTE_FINDED"]:
			self.relay_note_finded()
		elif cmd_flag == HANDSHAKE_COMMAND["RENDEZVOUS_ESTABLISHED"]:
			self.rendezvous_established()
		elif cmd_flag == HANDSHAKE_COMMAND["CIRCUIT_TERMINATED"]:
			pass
		else:
			logging.error("Unknown type of handshake packet type.")


	def relay_note_finded(self):
		circuit_id = self.current_handle.get_circuit_id()
		if circuit_id not in self._establishing_circuit:
			logging.error('Client received an unknown packet.')
			return -1
		current_circuit = self._establishing_circuit[circuit_id]
		dest = current_circuit.dest
		if dest == self.current_handle.get_fixed_route_table()[-1]:
			# a circuit has successfully established.
			del self._establishing_circuit[circuit_id]
			router_table = copy.deepcopy(self.current_handle.get_fixed_route_table())
			router_table.reverse()
			current_circuit.set_route_table(router_table)
			self._established_circuit[dest] = current_circuit
			#self.send_payload(dest) #TODO:
			pass

		else:
			# a circuit needs to be further extended.
			self.extend_a_circuit(current_circuit)


	def gen_payload(self,circuit_id, route_table, length):
		if length == 0:
			return []
		packet_buffer = []
		p_id = self._packet_id
		p_id = circuit_id + ':' + str(p_id)
		p_seq = 0
		self._packet_id += 1
		packet_count = int(length / 512) + 1
		for i in range(packet_count):
			pl_packet = Packet.PayloadPacket(p_id, p_seq, packet_count)
			p_seq += 1
			pl_packet.set_fixed_route_table(route_table)
			packet_buffer.append(pl_packet)
		return packet_buffer


	def send_payload(self):
		for circuit_id in self._rend_circuit:
			if circuit_id in self._send_content:
				length = self._send_content[circuit_id]
				if length == 0:
					continue
				route_table = self._rend_circuit[circuit_id]
				packet_buffer = self.gen_payload(circuit_id, route_table, length)
				for _ in packet_buffer:
					self.send(route_table[1], _)
				self._send_content[circuit_id] = 0

	def parse_payload_packet(self):
		packet_id = self.current_handle.get_packet_id()
		packet_seq = self.current_handle.get_packet_sequence()
		packet_total = self.current_handle.get_packet_total()
		if packet_id in self._recv_buffer:
			self._recv_buffer[packet_id].append(packet_seq)

		else:
			self._recv_buffer[packet_id] = [packet_seq]
		if len(self._recv_buffer[packet_id]) == packet_total:
			print 'payload receives successfully.'





	def send_to_server(self, length, server_id):
		# step1: decide a unique circuit identification
		current_id = random.randint(0, pow(2, 32) - 1)
		current_id = str(current_id) + ':' + str(server_id)
		temp = self._current_circuit_count

		self._current_circuit_count += 1
		rend_node_id = self.get_a_rend_node()
		print 'chosen rend: %d' % rend_node_id.id

		# step2: inform the server the identification and rend point.
		self.send_rend_inform_packet(server_id, rend_node_id.id, current_id)

		# step3: new a circuit to the rend point.
		self.new_a_circuit(current_id, rend_node_id.id, 2)

		# step4: wait the circuit established successfully and send the actual payload
		self._send_content[current_id] = length
		print 'send_to_server over'

	def resend_process(self, current_time):
		ack_count = len(self._ack_waited_list)
		if ack_count == 0:
			return
		for index in self._ack_waited_list:
			_ = self._ack_waited_list[index]
			if current_time - _[0] > self.resend_max_interval:
				if _[2] > self.resend_max_times:
					logging.info('[%d} packet drop for exceed the maximum resend times.' % self.id)
					del self._ack_waited_list[index]
				else:
					global_send(_[1])
					_[0] = current_time
					_[2] += 1

	def send(self, dest, pkt):  #dest is the ip of receiver point 
		pkt.set_from(self.id)
		pkt.set_to(dest)
		pkt.set_seq(self.seq)
		self._ack_waited_list[self.seq] = [get_current_time(), pkt, 0]
		self.seq += 1
		global_send(pkt)


	def recv(self, src, pkt):
		if isinstance(pkt, Packet.ACKPacket):
			self._ack_buffer.append(pkt)
			return SUCCESS

		# Assume that client's buffer will not be full.
		self._buffer_used += pkt.get_length()
		self._buffer.append(pkt)


	def parse_ack_packet(self):
		current_time = get_current_time()
		seq = self.current_handle.get_seq()
		src = self.current_handle.get_from()
		if seq in self._ack_waited_list:
			del self._ack_waited_list[seq]
		else:
			logging.error("Cannot find related packet record. seq:[%d]." %seq)

	def send_ack_pkt(self, pkt):
		seq = pkt.get_seq()
		recv = pkt.get_from()
		reply = Packet.ACKPacket(seq, self.id, recv)
		global_send(reply)

	def handle(self):
		current_time = get_current_time()
		self.resend_process(current_time)
		for _ in self._ack_buffer:
			self.current_handle = _
			self.parse_ack_packet()
		self._ack_buffer = []
		if self._buffer_used == 0:
			return 
		if current_time < self._next_trans_time:
			return
		self.current_handle = self._buffer[0]
		self._buffer.remove(self.current_handle)
		self._buffer_used -= self.current_handle.get_length()
		self.send_ack_pkt(self.current_handle)
		if self._buffer:
			self._next_trans_time = current_time + 1.0 * self._buffer[0].get_length() / (1024 * self._bandwidth)

		if isinstance(self.current_handle, Packet.PayloadPacket):
			self.parse_payload_packet()
		elif isinstance(self.current_handle, Packet.HandshakePacket):
			self.parse_handshake_packet()
		else:
			logging.info("Unknown packet type.")
		self.send_payload()


