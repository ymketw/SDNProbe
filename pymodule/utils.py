from ryu.ofproto import ether, inet
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, tcp, vlan, mpls

import sys 
import time
import cPickle
import copy
import random
import datetime
from array import array

from graph_tool.all import *
from topology import *
from testpacket import *
from switch import *
from rule import *

LOG = '../log/'

def beep():
    for i in xrange(5):
        time.sleep(0.2)
        print '\a'
        #sys.stdout.write('\a')

def to_dpid(switch_id):
     return switch_id+1

def to_switchid(dpid):
    return dpid-1
               

def initialize_adding_rules(testpackets, adding_path_number=1, is_random=False, is_shuffle=False):
    adding_ruleid_set = set()
    testpackets_size = len(testpackets)
    testpackets_list = testpackets.items()
    if is_random: random.shuffle(testpackets_list)
    
    for i, tp in testpackets_list[-adding_path_number:]:
        for rule_id in tp.rule_ids:
            adding_ruleid_set.add(rule_id)
        del testpackets[i]   

    adding_ruleid = list(adding_ruleid_set)
    if is_shuffle: random.shuffle(adding_ruleid)
    return adding_ruleid_set, adding_ruleid, testpackets

def initialize_deleting_rules(testpackets, deleting_path_number=1, is_random=False, is_shuffle=False):
    deleting_ruleid = set()
    testpackets_list = testpackets.items()
    if is_random: random.shuffle(testpackets_list)

    for i, tp in testpackets_list[-deleting_path_number:]:
        for rule_id in tp.rule_ids:
            deleting_ruleid.add(rule_id)

    deleting_ruleid = list(deleting_ruleid)
    if is_shuffle: random.shuffle(deleting_ruleid)
    return deleting_ruleid

def generate_testpacket(ip, tcp_src):
    p = packet.Packet()
    p.add_protocol(ethernet.ethernet(ethertype=0x800))
    #p.add_protocol(ethernet.ethernet(ethertype=0x8847))
    #p.add_protocol(mpls.mpls(label=tcp_src))
    #p.add_protocol(vlan.vlan(vid=vid+1501, ethertype=0x800))
    p.add_protocol(ipv4.ipv4(src=ip, proto=inet.IPPROTO_TCP))
    p.add_protocol(tcp.tcp(src_port=tcp_src))
    p.serialize()
    #pkt = packet.Packet(p.data)
    #for ele in pkt.protocols:
    #    print ele
    return p

def generate_packetout(tp, datapaths, rules):
    p = generate_testpacket(tp.get_header(), tp.get_unique_header())
    dp = datapaths[to_dpid(rules[tp.rule_ids[0]].get_switch_id())]
    parser = dp.ofproto_parser
    ofproto = dp.ofproto

    in_port = to_dpid(rules[tp.rule_ids[0]].get_in_port())
    buffer_id = dp.ofproto.OFP_NO_BUFFER
    actions = [parser.OFPActionOutput(ofproto.OFPP_TABLE)]
    out = parser.OFPPacketOut(datapath=dp, in_port=in_port, actions=actions, buffer_id=buffer_id, data=p.data)
    return dp, out

def initialize_testpackets(testpackets, datapaths, rules):
    packetouts = {}
    send_tpindex = set()
    header_tpindex = {}
    print 'Initialize test packets'
    for i, tp in testpackets.iteritems():
        header_tpindex[(rules[tp.rule_ids[-1]].get_switch_id(), tp.get_header())] = tp.index
        send_tpindex.add(tp.index)
        dp, out = generate_packetout(tp, datapaths, rules)
        packetouts[tp.index] = (dp, out)
    time.sleep(1)
    print 'Finish initialize test packets'
    return packetouts, send_tpindex, header_tpindex



def initialize_opt_testpackets(topology_graph, testpackets, datapaths, rules):
    new_testpackets = {}
    packetouts = {}
    send_tpindex = set()
    header_tpindex = {}
    switch_path = {}
    switch_path_ptr = {}
    bridging = {}

    print 'Initialize test packets'
    #construct the switch_path
    for i, tp in testpackets.iteritems():
        start_rule = rules[tp.rule_ids[0]]
        if start_rule.get_switch_id() not in switch_path:
            switch_path[start_rule.get_switch_id()] = []
            switch_path_ptr[start_rule.get_switch_id()] = 0
        switch_path[start_rule.get_switch_id()].append(tp)

    #sorting
    for k, v in switch_path.iteritems():
        switch_path[k].sort(key=lambda x : len(x.rule_ids), reverse=True)

    #search
    def find_start_switch():
        for v in topology_graph.vertices():
            if int(v) in switch_path and switch_path_ptr[int(v)] < len(switch_path[int(v)]):
                start_switch = int(v)
                return start_switch
        return -1

    ori_count = 0  
    path_count = 0
    start_switch = find_start_switch()
    last_rule_id = -1
    while True:
        tp = switch_path[start_switch][switch_path_ptr[start_switch]]
        end_switch = rules[tp.rule_ids[-1]].get_switch_id()
        is_find = False
        switch_path_ptr[start_switch] += 1
        ori_count += 1
        for neighbor in topology_graph.vertex(end_switch).all_neighbours():
            if int(neighbor) in switch_path and switch_path_ptr[int(neighbor)] < len(switch_path[int(neighbor)]):
                start_switch = int(neighbor)
                is_find = True
                break
        if not is_find:
            path_count += 1
            start_switch = find_start_switch()
        elif last_rule_id != -1:
            bridging[last_rule_id] = tp
        if start_switch == -1:
            break
        last_rule_id = tp.rule_ids[-1]

    print 'number of test packets:', ori_count
    print 'number of test packets with optimization:', path_count

    #for k, v in switch_path.iteritems():
    #    print 'switch_id:', k
    #    for tp in switch_path[k]:
    #        print tp.rule_ids

    #for i, tp in testpackets.iteritems():
    #    header_tpindex[(rules[tp.rule_ids[-1]].get_switch_id(), tp.get_header())] = tp.index
    #    send_tpindex.add(tp.index)
    #    dp, out = generate_packetout(tp, datapaths, rules)
    #    packetouts[tp.index] = (dp, out)
    #time.sleep(1)
    print 'Finish initialize test packets'
    #return new_testpackets, packetouts, send_tpindex, header_tpindex
    return packetouts, send_tpindex, header_tpindex, bridging


#def write_detection_delay(filename, fault_num, detection_delay, fault, traffic_rate, packet_count, threshold, prob=1.0):
#    filename = LOG + filename + '.detection_delay'
#    with open(filename, 'a') as f:
#        f.write("%s | " % (datetime.datetime.now()))
#        f.write("prob: %f | " % (prob))
#        f.write("rate: %f | " % (traffic_rate / 1024.0))
#        f.write("count: %d | " % (packet_count))
#        f.write("thres: %d | " % (threshold))
#        f.write("%d " % (fault_num))
#        for i in fault:
#            f.write(str(i) + ' ')
#        f.write("%f\n" % (detection_delay))
#
#        #if is_persistent:
#        #    f.write("%s --- " % (datetime.datetime.now()))
#        #    f.write("%d " % (fault_num))
#        #    for i in persistent_fault:
#        #        f.write(str(i) + ' ')
#        #    f.write("%f\n" % (detection_delay))
#        #else:
#        #    f.write("%d %f %f\n" % (fault_num, detection_delay, prob))
#
#def write_traffic(filename, traffic):
#    filename = LOG + filename + '.traffic'
#    with open(filename, 'w') as f:
#        for pkts in traffic:
#            f.write(str(pkts) + '\n')
#
#def write_controller_status(status):
#    '''
#    status == 0: not finished init
#    status == 1: finished init
#    '''
#    with open('controller.status', 'w') as f:
#        f.write(str(status))
#
#def write_adding_delay(filename, delays):
#    filename = LOG + filename + '.adding'
#    with open(filename, 'a') as f:
#        for i, d in enumerate(delays):
#            f.write('%d %f\n' % (i, d))
#
#def write_deleting_delay(filename, delays):
#    filename = LOG + filename + '.deleting'
#    with open(filename, 'a') as f:
#        for i, d in enumerate(delays):
#            f.write('%d %f\n' % (i, d))
#
#
#def read_persistent_fault_num():
#    with open('persistent_fault_num', 'r') as f:
#        num = f.read().strip()
#    return int(num)

#for naive controller
def read_persistent_fault_round():
    with open('persistent_fault_round', 'r') as f:
        r = f.read().strip()
    return int(r)
