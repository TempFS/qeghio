import Packet
from const import *
from channel import global_send, current_time
new_online_router = []
new_offline_router = []


class DirectoryServer():
	def __init__(self):
		self._global_table = {}
	def set_global_table(self, global_table):
		self._global_table = global_table
	def update_global_table(self):
		global new_online_router
		global new_offline_router
		for _ in new_offline_router and (_.id in self._global_table):
			if _.status == OFFLINE:
				del self._global_table[_.id]
		for _ in new_online_router:
			if _.status == ONLINE and (_.id not in self._global_table):
				self._global_table[_.id] = _
		new_online_router = []
		new_offline_router = []
	def get_global_table(self):
		return self._global_table
	def get_router_object_by_id(self, id):
		return self._global_table[id]

d = DirectoryServer()


Center_Directory_Server = DirectoryServer()


class RelayRouter():
	def __init__(self, id, ip, bandwidth, region, buffer_size, flag, status):
		self.id = id
		self.ip = ip
		self._bandwidth = bandwidth   					# KB/s
		self.region = region
		self._buffer_size = buffer_size 				# max buffer size
		self._fastnote_table = {}
		self._flag = flag
		self._global_table = []							# a table recording all of the router info, which is got from DirectoryServer.
		self._status = status 							# ONLINE / OFFLINE
		self._ack_waited_list = {}						# a list recording the seq of packets that have not received ack.
		self._ack_buffer = []								# a buffer to reveive ack packet
		self.seq = 0
		self._buffer = []
		self._buffer_used = 0
		self._next_trans_time = 0
		self.online()

	def online(self):
		self.status = ONLINE
		new_online_router.append(self)

	def offline(self):
		self.status = OFFLINE


	def get_global_table(self):
		self._global_table = Center_Directory_Server.get_global_table()


	def find_a_relay_note(self):
		reply = HandshakePacket(0, str(HANDSHAKE_COMMAND["RELAY_NOTE_FINDED"]) + str(self.id))
		return_route_table = self.current_handle.get_fixed_route_table().reverse()
		reply.set_fixed_route_table(return_route_table)
		self.send(self.current_handle.get_from(), reply)

	def relay_note_finded(self):
		# The Router cannot achieve this kind of handshake payload packet.
		logging.error("Router receives a RELAY_NOTE_FINDED packet.")

	def extend_circuit(self):
		reply = HandshakePacket(0, str(HANDSHAKE_COMMAND["CIRCUIT_EXTENDED"]) + str(self.id))
		return_route_table = self.current_handle.get_fixed_route_table().reverse()
		reply.set_fixed_route_table(return_route_table)
		self.send(self.current_handle.get_from(), reply)
		pass

	def circuit_extended(self):
		pass

	def terminate_circuit(self):
		pass

	def circuit_terminated(self):
		pass


	def parse_handshake_packet(self):
		hspkt = self.current_handle
		next_rp = hspkt.get_next_route()
		if next_rp != 0:
			self.send(next_rp, hspkt)
			return

		payload = hspkt.get_payload()
		cmd_flag = int(payload[0])
		if cmd_flag == HANDSHAKE_COMMAND["FIND_A_RELAY_NOTE"]:
			self.find_a_relay_note()
		elif cmd_flag == HANDSHAKE_COMMAND["RELAY_NOTE_FINDED"]:
			self.relay_note_finded()
		elif cmd_flag == HANDSHAKE_COMMAND["EXTEND_CIRCUIT"]:
			self.extend_circuit()
		elif cmd_flag == HANDSHAKE_COMMAND["CIRCUIT_EXTENDED"]:
			self.circuit_extended()
		elif cmd_flag == HANDSHAKE_COMMAND["TERMINATE_CIRCUIT"]:
			self.terminate_circuit()
		elif cmd_flag == HANDSHAKE_COMMAND["CIRCUIT_TERMINATED"]:
			self.circuit_terminated()
		else:
			logging.error("Unknown type of handshake packet type.")


	def parse_payload_packet(self):
		pkt = self.current_handle
		next_rp = pkt.get_next_route()
		if next_rp != 0:
			self.send(next_rp, pkt)
			return
		logging.error("A payload packet terminate in the middle of onion router.")


	def parse_ack_packet(self):
		current_time = get_current_time()
		seq = self.current_handle.get_seq()
		src = self.current_handle.get_from()
		if seq in self._ack_waited_list:
			tmp = self._ack_waited_list[seq]
			self._fastnote_table[src] = current_time - tmp
			del self._ack_waited_list[seq]
		else:
			logging.error("Cannot find related packet record. seq:[%d]." %seq)

	def send_ack_pkt(self, pkt):
		seq = pkt.get_seq()
		recv = pkt.get_from()
		reply = Packet.ACKPacket(seq, self.id, recv)
		global_send(reply)

	def send(self, dest, pkt):  #dest is the ip of receiver point 

		pkt.set_from(self.ip)
		pkt.set_to(dest)
		pkt.set_seq(self.seq)
		self.seq += 1
		self._ack_waited_list[seq] = get_current_time()
		global_send(pkt)

	def recv(self, src, pkt):
		temp = self._buffer_used + pkt.get_length()
		if self._buffer_size < temp:
			logging.info("Router[%x] discard the packet for the buffer is full." % self.id)
			return FAILURE
		self._buffer_used = temp
		self._buffer.append(pkt)
		return SUCCESS


	def handle(self):
		current_time = get_current_time()
		for _ in self._ack_buffer:
			self.current_handle = _
			self.parse_ack_packet()
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















