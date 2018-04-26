import logging
import sys

current_time = 0

def add_a_timeslice():
	global current_time
	current_time += 1

def get_current_time():
	global current_time
	return current_time
time_slice = 1  #1ms
FAILURE = -1
SUCCESS = 0
TOR_PACKET_LENGTH = 512

HANDSHAKE_COMMAND = {
	"FIND_A_RELAY_NOTE" : 0x1,
	"RELAY_NOTE_FINDED" : 0x2,
	"EXTEND_CIRCUIT" : 0x3,
	"CIRCUIT_EXTENDED" : 0x4,
	"TERMINATE_CIRCUIT" : 0x5,
	"CIRCUIT_TERMINATED" : 0x6
}

# Note Running Status
ONLINE = 0
OFFLINE = -1

LOG_FORMAT = "%(levelname)s - %(message)s"
logging.basicConfig(filename='log.txt', level=logging.DEBUG, format=LOG_FORMAT)