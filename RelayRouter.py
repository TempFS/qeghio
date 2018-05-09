import Packet
from const import *
from channel import global_send, current_time, global_resend
import client
import copy
new_online_router = []
new_offline_router = []


class DirectoryServer():
	def __init__(self):
		self._global_table = {}
		self._client_table = {}
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
		if id in self._global_table:
			return self._global_table[id]
		if id in self._client_table:
			return self._client_table[id]


d = DirectoryServer()


Center_Directory_Server = DirectoryServer()


class RelayRouter():
	def __init__(self, id, bandwidth, region, buffer_size, flag, status):
		self.id = id
		self.ip = id
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
		self._rend_circuit_id = 0
		self._circuit_map = {}
		self._rend_establishing_table = {}
		self._rend_established_table = {}      #{circuit_id : circuit_id}
		self.online()
 		self.resend_max_interval = 50000
		self.resend_max_times = 10
		self.discard_buffer = []
	def online(self):
		self.status = ONLINE
		new_online_router.append(self)

	def offline(self):
		self.status = OFFLINE


	def get_global_table(self):
		self._global_table = Center_Directory_Server.get_global_table()


	def find_a_relay_note(self):
		c_id = self.current_handle.get_circuit_id()
		reply = Packet.HandshakePacket(c_id, str(HANDSHAKE_COMMAND["RELAY_NOTE_FINDED"]) + str(self.id))
		route_table = copy.deepcopy(self.current_handle.get_fixed_route_table())
		route_table.reverse()
		reply.set_fixed_route_table(route_table)
		self.send(self.current_handle.get_from(), reply)

	def relay_note_finded(self):
		# The Router cannot achieve this kind of handshake payload packet.
		logging.error("[%d]Router receives a RELAY_NOTE_FINDED packet."%self.id)

	def extend_circuit(self):
		reply = Packet.HandshakePacket(0, str(HANDSHAKE_COMMAND["CIRCUIT_EXTENDED"]) + str(self.id))
		return_route_table = copy.deepcopy(self.current_handle.get_fixed_route_table())
		return_route_table.reverse()
		reply.set_fixed_route_table(return_route_table)
		self.send(self.current_handle.get_from(), reply)
		pass

	def circuit_extended(self):
		pass

	def establish_rendezvous(self):
		rend_id = self.current_handle.get_circuit_id()
		current_circuit_id = rend_id
		prefix = rend_id.split(':')[0]
		self._rend_circuit_id += 1

		flag = 0   # send it to the client, 0 means its communication object has not prepared; 1 means its communication object has prepared.
		if prefix in self._rend_establishing_table:
			target_circuit_id = self._rend_establishing_table[prefix]
			self._rend_established_table[current_circuit_id] = target_circuit_id
			self._rend_established_table[target_circuit_id] = current_circuit_id
			del self._rend_establishing_table[prefix]
			flag = 1
			# inform the target client that the other side has prepared.
			#ASSERT(target_circuit_id in self._circuit_map)
			target_cirobj = self._circuit_map[target_circuit_id]
			info_reply = Packet.HandshakePacket(target_circuit_id, str(HANDSHAKE_COMMAND["RENDEZVOUS_ESTABLISHED"]) + str(flag) + str(target_circuit_id))
			info_reply.set_fixed_route_table(target_cirobj.route_table)
			self.send(target_cirobj.route_table[1], info_reply)

		else:
			
			self._rend_establishing_table[prefix] = rend_id
			flag = 0


		reply = Packet.HandshakePacket(rend_id, str(HANDSHAKE_COMMAND["RENDEZVOUS_ESTABLISHED"]) + str(flag) + str(current_circuit_id))
		route_table = copy.deepcopy(self.current_handle.get_fixed_route_table())

		route_table.reverse()
		cirobj = client.Circuit(current_circuit_id, route_table, None, None)
		self._circuit_map[current_circuit_id] = cirobj
		reply.set_fixed_route_table(route_table)
		self.send(self.current_handle.get_from(), reply)
		pass

	def rendezvous_established(self):
		pass


	def parse_handshake_packet(self):
		hspkt = self.current_handle
		next_rp = hspkt.get_next_route()
		if next_rp != 0 and next_rp != self.id:
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
		elif cmd_flag == HANDSHAKE_COMMAND["ESTABLISH_RENDEZVOUS"]:
			self.establish_rendezvous()
		elif cmd_flag == HANDSHAKE_COMMAND["RENDEZVOUS_ESTABLISHED"]:
			self.rendezvous_established()
		else:
			logging.error("Unknown type of handshake packet type.")


	def parse_payload_packet(self):
		pkt = self.current_handle
		next_rp = pkt.get_next_route()
		if next_rp != 0:
			self.send(next_rp, pkt)
			return
		p_id = pkt.get_packet_id().split(':')
		c_id = p_id[0]+':'+p_id[1]

		s_id = self._rend_established_table[c_id]
		if s_id not in self._circuit_map:
			logging.error('An unkown circuit. s_id:[%s] self.id:[%d]' %(s_id, self.id))
		route_table = self._circuit_map[s_id].get_route_table()

		#logging.error("A payload packet terminate in the middle of onion router.")
		pkt.set_fixed_route_table(route_table)
		self.send(route_table[1], pkt)



	def parse_ack_packet(self):
		current_time = get_current_time()
		seq = self.current_handle.get_seq()
		src = self.current_handle.get_from()
		if seq in self._ack_waited_list:
			tmp = self._ack_waited_list[seq][0]
			self._fastnote_table[src] = current_time - tmp
			del self._ack_waited_list[seq]
		else:
			logging.error("[%d]Cannot find related packet record. seq:[%d] from:[%d]." %(self.id,seq, src))

	def resend_process(self, current_time):
		ack_count = len(self._ack_waited_list)
		if ack_count == 0:
			return
		drop_buffer = []
		for index in self._ack_waited_list:
			_ = self._ack_waited_list[index]
			if current_time - _[0] > self.resend_max_interval:
				if _[2] > self.resend_max_times:
					logging.info('[%d] packet drop for exceed the maximum resend times.' % self.id)
					drop_buffer.append(index)

				else:
					_[1].set_resend_flag()
					logging.info('[%d] packet resend.' % self.id)
					global_resend(_[1])
					_[0] = current_time
					_[2] += 1
		for index in drop_buffer:
			del self._ack_waited_list[index]



	def send_ack_pkt(self, pkt):
		seq = pkt.get_seq()
		recv = pkt.get_from()
		reply = Packet.ACKPacket(seq, self.id, recv)
		global_send(reply)

	def send(self, dest, pkt):  #dest is the ip of receiver point 

		pkt.set_from(self.ip)
		pkt.set_to(dest)
		pkt.set_seq(self.seq)
		self._ack_waited_list[self.seq] = [get_current_time(), pkt, 0]
		self.seq += 1
		global_send(pkt)


	def recv(self, src, pkt):
		if isinstance(pkt, Packet.ACKPacket):
			self._ack_buffer.append(pkt)
			return SUCCESS
		temp = self._buffer_used + pkt.get_length()
		if self._buffer_size < temp:
			logging.info("Router[%x] discard the packet for the buffer is full." % self.id)
			pkt_info = [pkt._from, pkt._seq]
			self.discard_buffer.append(pkt_info)

			return FAILURE
		if pkt.resend_flag == True:
			resend_mode = False
			for _ in self.discard_buffer:
				if _[0] == pkt._from and _[1] == pkt._seq:
					self.discard_buffer.remove(_)
					resend_mode = True
			if resend_mode == False:
				return SUCCESS

		self._buffer_used = temp
		self._buffer.append(pkt)
		return SUCCESS


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
















