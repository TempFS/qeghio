import numpy as np
import RelayRouter
#from RelayRouter import d
import Packet
import client
import channel
import random
from const import *
local_delay = 5
client_count = 5000
p = 0.3
def load_region_distribution():
    region_distribution = {}
    fp = open('region_distribution.txt', 'r')
    lines = fp.readlines()
    for line in lines:
        tmp = line.split('\t')
        if len(tmp) != 2:
            continue
        region = tmp[0]
        distri = tmp[1]
        if distri[-1] == '\n':
            distri = distri[:-1]

        region_distribution[region] = int(distri)
    fp.close()
    return region_distribution

def random_send_packet(c, flag):
    if flag == False:
        r = random.random()
        packet_length = 50*1024
    else:
        r = 0
        packet_length = 1
    if r > p:
        return
    sender = random.choice(c)
    receiver = random.choice(c)
    while receiver == sender:
        receiver = random.choice(c)
    sender.send_to_server(packet_length, receiver.id)

def main():
    region_distribution = load_region_distribution()
    region_table = []
    p = []
    channel.ch.load_delay('region_delay.txt')
    i = 1
    for region in region_distribution:
        j = 0
        region_table.append(region)
        region_node_count = region_distribution[region] / 4
        if region_node_count == 0:
            region_node_count = 1
        while j < region_node_count:
            p.append(RelayRouter.RelayRouter(i, 4*random.randint(2*1024*1024, 20*1024*1024), region, 200*1024*1024, 0, ONLINE))
            i+=1
            j+=1
    RelayRouter.d.update_global_table()
    total_delay = i
    c = []
    for i in range(client_count):
        tmp = client.Client(10000+i, 2000000,random.choice(region_table), 0.1)
        tmp._entrynode = []
        rnd = random.randint(1,total_delay-4)
        tmp._entrynode.append(rnd)
        tmp._entrynode.append(rnd + 1)
        tmp._entrynode.append(rnd + 2)
        c.append(tmp)

    RelayRouter.d.update_global_table()
    ct = get_current_time()
    for _ in p:
        _.generate_fast_note_table()
    while ct < 500000:
        print ct
        if ct % 1000 == 0:
            for _ in p:
                _.dump_fast_note_table()


        random_send_packet(c, False)
        channel.ch.handle()

        for _ in p:
            _.handle()
        for _ in c:
            _.handle()

        # c2.send_to_server(5000, 10000)

        add_a_timeslice()
        ct = get_current_time()
if __name__ == '__main__':
    main()

