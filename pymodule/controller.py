from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether, inet
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, tcp, vlan, mpls
from ryu.lib import hub

import os, sys
sys.dont_write_bytecode = True
import time
import timeit
import cPickle
import copy
import random
from collections import defaultdict

from graph_tool.all import *
from topology import *
from testpacket import *
from switch import *
from rule import *

from utils import *
from attack import *

from token_bucket import TokenBucket

class Detection(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    DEBUG_MSG = False
    TRAFFIC_MSG = False
    INCREMENTAL_ADDING = False
    INCREMENTAL_DELETING = False
    DETOUR = False
    MONITOR = True
    INCREMENTAL_INDEX = 50000
    PERSISTENT_NUM = 0
    NONPERSISTENT_NUM = 0
    THRESHOLD = -3
    TRAFFIC_RATE = 250 * 1024 #(B/s)
    PACKET_SIZE = 64 #(Bytes)
    CONFIG_NAME = 'config/config'
    FILENAME = ''
    

    def __init__(self, *args, **kwargs):
        super(Detection, self).__init__(*args, **kwargs)
        random.seed()
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
        sys.stdin = os.fdopen(sys.stdin.fileno(), 'r', 0)

        print >> sys.stderr, 'Loading topology'
        self.read_config()
        self.rules = load_rules(Detection.FILENAME + '.rules.pkl')
        self.topology_graph = load_topology(Detection.FILENAME + '.graphml')
        self.testpackets = load_testpackets(Detection.FILENAME + '.testpackets.pkl')

        self.datapaths = {}
        self.packetouts = {}
        self.packetouts_store = {}

        self.reputation = defaultdict(int)

        #record test packet
        #key is (switch_id, header), value is tp_index
        self.heaer_tpindex = {}
        #key is test packet index 
        self.send_tpindex = set()
        self.recv_tpindex = set()
        self.send_tpindex_store = []

        self.ori_tetspackets_size = len(self.testpackets)
        self.inc_testpackets_size = 0

        #for incremental adding rules
        self.adding_ruleid_set = set()
        self.adding_ruleid = list()
        if Detection.INCREMENTAL_ADDING:
            self.adding_ruleid_set, self.adding_ruleid, self.testpackets = initialize_adding_rules(self.testpackets, adding_path_number=800, is_random=True, is_shuffle=True)
        self.adding_ruleid = self.adding_ruleid[:3000]
        #print len(self.adding_ruleid), 'adding rules'
        if Detection.DEBUG_MSG: 'Adding-rule id:', self.adding_ruleid

        #for incremental deleting rules
        self.deleting_ruleid = list()
        if Detection.INCREMENTAL_DELETING:
            self.deleting_ruleid = initialize_deleting_rules(self.testpackets, deleting_path_number=700, is_random=True, is_shuffle=True)
        self.deleting_ruleid = self.deleting_ruleid[:3000]
        #print len(self.deleting_ruleid), 'deleting rules' 
        if Detection.DEBUG_MSG: 'Deleting-rule id:', self.deleting_ruleid

        #simulate the attacker
        #key is rule id which is compromised by switch
        self.persistent_fault = initialize_persistent_fault(Detection.PERSISTENT_NUM, self.rules, self.testpackets)
        self.nonpersistent_fault = initialize_nonpersistent_fault(Detection.NONPERSISTENT_NUM, self.rules, self.testpackets, self.persistent_fault)
        self.catch_fault = set()

        if Detection.PERSISTENT_NUM > 0:
            print >> sys.stderr, 'Presistent fault:', self.persistent_fault 
        #print 'Non-presistent fault:', self.nonpersistent_fault 

        #for recording traffic 
        self.packet_counter = 0
        self.traffic = []
        self.traffic_start_time = 0.0
        self.bucket = TokenBucket(Detection.TRAFFIC_RATE, Detection.TRAFFIC_RATE)

        #for experiment script
        #write_controller_status(1)
     
        print >> sys.stderr, 'Waiting for switches to connect...'

    def read_config(self):
        with open(Detection.CONFIG_NAME, 'r') as f:
            for line in f:
                var, val = line.strip().split('=') 
                if var == 'TOPOLOGY_FILE': Detection.FILENAME += val
                if var == 'DETECTION_THRESHOLD': Detection.THRESHOLD = 0-int(val)
                if var == 'TEST_PACKET_RATE(K/bytes)': Detection.TRAFFIC_RATE = int(val) * 1024
                if var == 'SIMULATE_ATTACK': Detection.PERSISTENT_NUM = int(val)
                if var == 'MONITOR': Detection.MONITOR = (val == 'True')


    def send_testpackets(self):
        print >> sys.stderr, '  Send test packets'
        for tp_index, (dp, out) in self.packetouts.iteritems():
            while not self.bucket.consume(Detection.PACKET_SIZE):
                pass
            dp.send_msg(out)

            self.packet_counter += 1
            if Detection.TRAFFIC_MSG and timeit.default_timer() - self.traffic_start_time >= 10:
                self.traffic.append(self.packet_counter / (timeit.default_timer() - self.traffic_start_time))
                self.packet_counter = 0
                self.traffic_start_time = timeit.default_timer()

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        dpid = datapath.id
        

        pkt = packet.Packet(msg.data)
        src = pkt.get_protocols(ethernet.ethernet)[0].src
        dst = pkt.get_protocols(ethernet.ethernet)[0].dst
        ipv4_src = pkt.get_protocols(ipv4.ipv4)[0].src
        ipv4_dst = pkt.get_protocols(ipv4.ipv4)[0].dst

        #print len(msg.data), sys.getsizeof(msg.data), sys.getsizeof(pkt)

        #self.logger.info("packet in dpid %s, %s, %s, %s, %s, %s", dpid, src, dst, ipv4_src, ipv4_dst, in_port)
        self.recv_tpindex.add(self.header_tpindex[(to_switchid(dpid), ipv4_src)])

    def slice_path(self, tp_index):
        print >> sys.stderr, "  Slice path"
        #slice path and testpacket
        middle = len(self.testpackets[tp_index].rule_ids) / 2
        if tp_index >= Detection.INCREMENTAL_INDEX:
            new_tp = TestPacket(self.inc_testpackets_size+Detection.INCREMENTAL_INDEX, self.testpackets[tp_index].prefix, self.testpackets[tp_index].rule_ids[middle:])
            self.inc_testpackets_size += 1
        else:
            new_tp = TestPacket(self.ori_tetspackets_size, self.testpackets[tp_index].prefix, self.testpackets[tp_index].rule_ids[middle:])
            self.ori_tetspackets_size += 1
        new_tp.unique_header = self.testpackets[tp_index].unique_header
        self.testpackets[tp_index].rule_ids = self.testpackets[tp_index].rule_ids[:middle]
        
        #update testpackets
        #self.testpackets.append(new_tp)
        self.testpackets[new_tp.index] = new_tp
        self.send_tpindex.add(new_tp.index)
        dp, out = generate_packetout(new_tp, self.datapaths, self.rules)
        self.packetouts[new_tp.index] = (dp, out)

        tp = self.testpackets[tp_index]
        self.header_tpindex[(self.rules[tp.rule_ids[-1]].get_switch_id(), tp.get_header())] = tp.index
        self.header_tpindex[(self.rules[new_tp.rule_ids[-1]].get_switch_id(), new_tp.get_header())] = new_tp.index

        #add test flow entry
        self.rules[tp.rule_ids[-1]].is_path_end = True
        rule = self.rules[tp.rule_ids[-1]]
        self.add_test_flow_entry(self.datapaths[to_dpid(rule.get_switch_id())], rule)

    def fault_localization(self):
        start_time = timeit.default_timer()
        self.traffic_start_time = timeit.default_timer()
        print >> sys.stderr, 'Start fault localization at', str(start_time)
        #self.send_testpackets()
        
        #time.sleep(10)
        while len(self.catch_fault) < Detection.PERSISTENT_NUM + Detection.NONPERSISTENT_NUM or Detection.TRAFFIC_MSG or Detection.MONITOR:
            if Detection.TRAFFIC_MSG and timeit.default_timer() - start_time >= 110:
                write_traffic(Detection.FILENAME_PREFIX, self.traffic)
                break
            self.send_testpackets()
            if Detection.TRAFFIC_MSG:
                continue
            time.sleep(0.3)
            #print "send tp index:", self.send_tpindex
            #print "recv tp index:", self.recv_tpindex
            suspected_tpindex = self.send_tpindex.difference(self.recv_tpindex)

            remove_tp_index = [key for key in self.packetouts]
            for i in remove_tp_index:
                if i not in suspected_tpindex:
                    self.packetouts_store[i] = self.packetouts[i]
                    self.send_tpindex_store.append(i)
                    del self.packetouts[i]
                    self.send_tpindex.remove(i)

            for i in suspected_tpindex:
                tp = self.testpackets[i]
                for rule_id in tp.rule_ids:
                    self.reputation[rule_id] -= 1
                if len(tp.rule_ids) > 1:
                    self.slice_path(i)
                elif self.reputation[tp.rule_ids[0]] <= Detection.THRESHOLD:
                    if Detection.DETOUR and tp.rule_ids[0] in self.detour_pair and self.detour_pair[tp.rule_ids[0]] != -1:
                        rand = random.randint(1, 10000)
                        self.detour_pair[tp.rule_ids[0]] = -1
                        Detection.PERSISTENT_NUM -= 1
                        if rand < 7500: 
                            continue
                    else:
                        if Detection.DETOUR:
                            current_time = timeit.default_timer() - start_time
                            fnr = len(self.persistent_fault - self.catch_fault) / float(len(self.persistent_fault))
                            self.detour_record.append((current_time, fnr))
                        print >> sys.stderr, 'Detect fault:', tp.rule_ids[0]
                        self.catch_fault.add(tp.rule_ids[0])
            


            if len(suspected_tpindex) == 0:
                for i in self.send_tpindex_store:
                    self.send_tpindex.add(i)
                    self.packetouts[i] = self.packetouts_store[i]
                self.send_tpindex_store = []
                self.packetouts_store = {}

                #self.reputation[i] -= 1
                #if self.reputation[i] <= Detection.THRESHOLD:
                #    if len(tp.rule_ids) == 1:
                #        print 'Detect fault:', tp.rule_ids[0]
                #        self.catch_fault.add(tp.rule_ids[0])
                #    else:
                #        self.reputation[i] = 0 
                #        self.slice_path(i)
            self.recv_tpindex.clear()
            #time.sleep(0.1)
 
        print >> sys.stderr,  "End fault localization"
        print >> sys.stderr, "  persistent fault", self.persistent_fault
        print >> sys.stderr, "  non-persistent fault", self.nonpersistent_fault
        print >> sys.stderr, "  catch fault", self.catch_fault
        end_time = timeit.default_timer()
        detection_delay = end_time - start_time
        #print >> sys.stderr, "End time", end_time
        print >> sys.stderr, "Detection delay", detection_delay
        #if Detection.PERSISTENT_NUM > 0 and Detection.NONPERSISTENT_NUM == 0:
        #    write_detection_delay(Detection.FILENAME_PREFIX, Detection.PERSISTENT_NUM, detection_delay, self.persistent_fault, Detection.TRAFFIC_RATE, self.packet_counter, Detection.THRESHOLD)
        #elif Detection.PERSISTENT_NUM == 0 and Detection.NONPERSISTENT_NUM > 0:
        #    write_detection_delay(Detection.FILENAME_PREFIX, Detection.NONPERSISTENT_NUM, detection_delay, self.nonpersistent_fault, Detection.TRAFFIC_RATE, self.packet_counter, Detection.THRESHOLD, prob=Detection.NONPERSISTENT_PROB)
        #beep()
        #write_controller_status(0)

        if (Detection.PERSISTENT_NUM > 0 or Detection.NONPERSISTENT_NUM > 0) and not Detection.DETOUR:
            os._exit(1)

    #@set_ev_cls(ofp_event.EventOFPSwitchFeatures, MAIN_DISPATCHER)
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[int(datapath.id)] = datapath
        if len(self.datapaths) == self.topology_graph.num_vertices():
            for dpid, dp in self.datapaths.iteritems():
                self.initialize_switch(dp)
                time.sleep(0.2)

            self.packetouts, self.send_tpindex, self.header_tpindex = initialize_testpackets(self.testpackets, self.datapaths, self.rules)
            self.ori_packetouts = self.packetouts
            self.ori_send_tp_index = copy.deepcopy(self.send_tpindex)
            #self.send_testpackets()
            #self.fault_localization()
            #time.sleep(10)
            fault_localize_thread = hub.spawn(self.fault_localization)
            attacker_thread = hub.spawn(self.simulate_nonpersistent_fault)
            if Detection.INCREMENTAL_ADDING: incremental_adding_thread = hub.spawn(self.simulate_incremental_adding)
            if Detection.INCREMENTAL_DELETING: incremental_deleting_thread = hub.spawn(self.simulate_incremental_deleting)
            #if Detection.DETOUR:
            #    detour_thread = hub.spawn(self.FN)

        #ofproto = datapath.ofproto
        #parser = datapath.ofproto_parser
        #match = parser.OFPMatch(in_port=78, eth_type=0x0800)
        #actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        #self.add_flow(datapath, 0, match, actions)
        return
        
        #Test
        #
        #
        #if datapath.id == to_dpid(72):
        #    match = parser.OFPMatch(in_port=to_dpid(48), eth_type=0x0800, ipv4_src=('179.60.196.0', '255.255.255.0'))
        #    #actions = [parser.OFPActionOutput(73, ofproto.OFPCML_NO_BUFFER)]
        #    actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        #    self.add_flow(datapath, 32768, match, actions)

        #if len(self.datapaths) == 10:
        #    time.sleep(1)
        #    #self.test_thread = hub.spawn(self._test)

        #    p = packet.Packet()
        #    p.add_protocol(ethernet.ethernet(ethertype=0x800))
        #    p.add_protocol(ipv4.ipv4(src='179.60.196.0'))
        #    p.add_protocol(tcp.tcp(src_port=1000, dst_port=2000))
        #    p.serialize()
        #    parser = self.datapaths[to_dpid(72)].ofproto_parser
        #    ofproto = self.datapaths[to_dpid(72)].ofproto
        #    actions = [parser.OFPActionOutput(ofproto.OFPP_TABLE)]
        #    out = parser.OFPPacketOut(datapath=self.datapaths[to_dpid(72)], in_port=to_dpid(48), 
        #                                buffer_id=self.datapaths[to_dpid(72)].ofproto.OFP_NO_BUFFER, actions=actions, data=p.data)
        #    #out = parser.OFPPacketOut(datapath=datapath, in_port=ofproto.OFPP_CONTROLLER)
        #    for i in xrange(1):
        #        self.datapaths[to_dpid(72)].send_msg(out)

    def initialize_switch(self, datapath):
        print >> sys.stderr, '---Initialize switch id:', to_switchid(datapath.id), 'datapath id:', datapath.id
        switch_id = to_switchid(datapath.id)
        switch = self.topology_graph.get_switch(switch_id)
        
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        for rule_id, rule in switch.get_flow_table(table_id=0).iteritems():
            #Ignore the rule to simulate persistent attack
            if rule_id in self.persistent_fault: continue

            #Ignore adding rule
            if rule_id in self.adding_ruleid_set: continue

            out_port = to_dpid(rule.get_out_port())
            priority = rule.get_priority()
            match = self.get_match(parser, rule)
            actions = [parser.OFPActionOutput(out_port, ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(datapath, priority, match, actions)
            if rule.is_path_end:
                self.add_test_flow_entry(datapath, rule)
            #if rule.is_path_start:
            #    self.start_path_rules[rule.get_path_index()] = rule

    def add_test_flow_entry(self, datapath, rule):
        if rule.get_id() in self.persistent_fault: return

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        output_rule = copy.deepcopy(rule)
        input_rule = copy.deepcopy(rule)
        sendback_rule = copy.deepcopy(rule)
        
        output_rule.set_table_id(output_rule.get_table_id()+1)
        output_rule.is_modified_output = True
        
        input_rule.set_inst_actions(Rule.GOTO_TABLE, [Rule.OUTPUT])
        input_rule.is_modified_input = True
        
        sendback_rule.set_table_id(sendback_rule.get_table_id()+1)
        sendback_rule.set_prefix(self.testpackets[sendback_rule.get_path_index()].get_prefix())
        sendback_rule.set_out_port(ofproto.OFPP_CONTROLLER)
        sendback_rule.set_priority(32768)
        sendback_rule.is_sendback = True
        self.network_sync_insert_rule(output_rule)
        self.network_sync_insert_rule(input_rule)
        self.network_sync_insert_rule(sendback_rule)

        #del original rule
        self.del_flow(datapath, rule.get_priority(), self.get_match(parser, rule), rule.get_table_id())
        
        #add new input goto table rule
        #self.add_flow(datapath, input_rule.get_priority(), self.get_match(parser, input_rule), [parser.OFPInstructionGotoTable(input_rule.get_table_id()+1)])
        inst = [parser.OFPInstructionGotoTable(output_rule.get_table_id())]
        mod = parser.OFPFlowMod(datapath=datapath, priority=input_rule.get_priority(), match=self.get_match(parser, input_rule), instructions=inst, table_id=input_rule.get_table_id())
        datapath.send_msg(mod)

        #add new output rule
        self.add_flow(datapath, output_rule.get_priority(), self.get_match(parser, output_rule), [parser.OFPActionOutput(to_dpid(output_rule.get_out_port()), ofproto.OFPCML_NO_BUFFER)], table_id=output_rule.get_table_id())

        #add new send back to control rule
        in_port = to_dpid(sendback_rule.get_in_port())
        if sendback_rule.get_prefix().find('/') == -1:
            ipv4_src = (sendback_rule.get_prefix(), '255.255.255.0')
        else:
            ipv4_src = (sendback_rule.get_prefix()[:sendback_rule.get_prefix().index('/')], '255.255.255.0')
        tcp_src = self.testpackets[sendback_rule.get_path_index()].get_unique_header()
        match = parser.OFPMatch(in_port=in_port, eth_type=0x800, ipv4_src=ipv4_src, ip_proto=inet.IPPROTO_TCP, tcp_src=tcp_src)
        #match = parser.OFPMatch(in_port=in_port, eth_type=0x8847, ipv4_src=ipv4_src, ip_proto=inet.IPPROTO_TCP, mpls_label=tcp_src)
        #vlan_vid = (0x1000 | self.testpackets[sendback_rule.get_path_index()].get_unique_header())
        #match = parser.OFPMatch(in_port=in_port, eth_type=0x800, ipv4_src=ipv4_src, ip_proto=inet.IPPROTO_VRRP, vlan_vid=vlan_vid)
        self.add_flow(datapath, sendback_rule.get_priority(), match, [parser.OFPActionOutput(sendback_rule.get_out_port(), ofproto.OFPCML_NO_BUFFER)], table_id=sendback_rule.get_table_id())

    #def del_test_flow_entry(self, rule):
    #    self.network_delete_rule(self.topology_graph.get_switch(rule.get_switch_id()).modified_input_rules[rule.id])
    #    self.network_delete_rule(self.topology_graph.get_switch(rule.get_switch_id()).modified_output_rules[rule.id])
    #    self.network_delete_rule(self.topology_graph.get_switch(rule.get_switch_id()).sendback_rules[rule.id])

    def get_match(self, parser, rule):
        in_port = to_dpid(rule.get_in_port())
        #####
        if rule.get_prefix()[-2:] == '32':
            ipv4_src = (rule.get_prefix()[:rule.get_prefix().index('/')], '255.255.255.255')
        elif rule.get_prefix().find('/') == -1:
            ipv4_src = (rule.get_prefix(), '255.255.255.0')
        else:
            ipv4_src = (rule.get_prefix()[:rule.get_prefix().index('/')], '255.255.255.0')
        return parser.OFPMatch(in_port=in_port, eth_type=0x800, ipv4_src=ipv4_src)
        #tcp_src = self.testpackets[rule.get_path_index()].get_unique_header()
        #if not rule.is_incremental:
        #    match = parser.OFPMatch(in_port=in_port, eth_type=0x800, ipv4_src=ipv4_src)
        #else:
        #    match = parser.OFPMatch(in_port=in_port, eth_type=0x800, ipv4_src=ipv4_src, ip_proto=inet.IPPROTO_TCP, tcp_src=tcp_src)
        #return match

    def add_flow(self, datapath, priority, match, actions, table_id=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst, table_id=table_id)
        datapath.send_msg(mod)

    def del_flow(self, datapath, priority, match, table_id=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, command=ofproto.OFPFC_DELETE, table_id=table_id, out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY)
        datapath.send_msg(mod)

    def network_insert_rule(self, rule):
        self.network_sync_insert_rule(rule)

        datapath = self.datapaths[to_dpid(rule.get_switch_id())]
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        out_port = to_dpid(rule.get_out_port())
        priority = rule.get_priority()
        match = self.get_match(parser, rule)
        actions = [parser.OFPActionOutput(out_port, ofproto.OFPCML_NO_BUFFER)]

        if Detection.DEBUG_MSG: print "Insert ", rule, rule.get_table_id()
        self.add_flow(datapath, priority, match, actions)

    def network_delete_rule(self, rule):
        self.network_sync_delete_rule(rule)
        datapath = self.datapaths[to_dpid(rule.get_switch_id())]
        parser = datapath.ofproto_parser
        if Detection.DEBUG_MSG: print "Delete ", rule, rule.get_table_id()
        self.del_flow(datapath, rule.get_priority(), self.get_match(parser, rule), table_id=rule.get_table_id())


    def network_sync_insert_rule(self, rule):
        if rule.is_incremental:
            self.topology_graph.get_switch(rule.get_switch_id()).add_incremental_rule(rule)
        if rule.is_sendback:
            self.topology_graph.get_switch(rule.get_switch_id()).add_sendback_rule(rule)
        if rule.is_modified_input:
            self.topology_graph.get_switch(rule.get_switch_id()).add_modified_input_rule(rule)
        if rule.is_modified_output:
            self.topology_graph.get_switch(rule.get_switch_id()).add_modified_output_rule(rule)
        if rule.is_deleted:
            self.topology_graph.get_switch(rule.get_switch_id()).add_deleted_rule(rule)

    def network_sync_delete_rule(self, rule):
        switch = self.topology_graph.get_switch(rule.get_switch_id())
        if rule.is_incremental and rule.id in switch.incremental_rules:
            del self.topology_graph.get_switch(rule.get_switch_id()).incremental_rules[rule.id]
        if rule.is_sendback:
            del self.topology_graph.get_switch(rule.get_switch_id()).sendback_rules[rule.id]
        if rule.is_modified_input:
            del self.topology_graph.get_switch(rule.get_switch_id()).modified_input_rules[rule.id]
        if rule.is_modified_output:
            del self.topology_graph.get_switch(rule.get_switch_id()).modified_output_rules[rule.id]
        #if rule.is_deleted:
        #    del self.topology_graph.get_switch(rule.get_switch_id()).deleted_rules[rule.id]


    def simulate_nonpersistent_fault(self):
        while len(self.catch_fault) < Detection.NONPERSISTENT_NUM:
            for rule_id in self.nonpersistent_fault:
                rule = self.rules[rule_id]
                dpid = to_dpid(rule.get_switch_id())
                datapath = self.datapaths[dpid]
                ofproto = datapath.ofproto
                parser = datapath.ofproto_parser
                #good or bad
                inst = []
                prob = random.uniform(0, 1)
                if prob > Detection.NONPERSISTENT_PROB:
                    if rule.is_path_end:
                        inst = [parser.OFPInstructionGotoTable(rule.get_table_id()+1)]
                    else:
                        actions = [parser.OFPActionOutput(to_dpid(rule.get_out_port()), ofproto.OFPCML_NO_BUFFER)]
                        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                mod = parser.OFPFlowMod(datapath=datapath, priority=rule.get_priority(), match=self.get_match(parser, rule), command=ofproto.OFPFC_ADD, \
                        instructions=inst, table_id=rule.get_table_id())
                datapath.send_msg(mod)
                #print rule.switch_id, prob, rule.is_path_end, inst
            time.sleep(1)

    def simulate_incremental_adding(self):
        delays = []
        for rule_id in self.adding_ruleid:
            rule = self.rules[rule_id]
            start_time = timeit.default_timer()
            self.simulate_adding_rule(rule)
            #time.sleep(1)
            end_time = timeit.default_timer()
            delays.append(end_time - start_time)
        #print "Average delay of adding one rule", (end_time - start_time) / float(len(self.adding_ruleid))
        #print "PacketOut number", len(self.packetouts)
        #write_adding_delay(Detection.FILENAME_PREFIX, delays)
        print 'Finish adding rules'
        os._exit(1)

    def simulate_adding_rule(self, rule):
        start_tp = None
        end_tp = None
        for i in xrange(self.inc_testpackets_size):
            if i+Detection.INCREMENTAL_INDEX not in self.testpackets: continue
            inc_tp = self.testpackets[i+Detection.INCREMENTAL_INDEX]
            start_rule = self.rules[inc_tp.rule_ids[0]]
            end_rule = self.rules[inc_tp.rule_ids[-1]]
            if rule.get_out_port() == start_rule.get_switch_id() and rule.get_prefix() == start_rule.get_prefix():
                start_tp = inc_tp
            if rule.get_in_port() == end_rule.get_switch_id() and rule.get_prefix() == end_rule.get_prefix():
                end_tp = inc_tp

        if Detection.DEBUG_MSG: print rule
        rule.is_incremental = True
        r_start = self.rules[start_tp.rule_ids[0]] if start_tp != None else None
        r_end = self.rules[end_tp.rule_ids[-1]] if end_tp != None else None
        #print 'Finish adding rules'
        if start_tp is not None and end_tp is not None:
            if Detection.DEBUG_MSG: print '--------------------------1'
            rule.path_index = start_tp.index
            self.testpackets[start_tp.index].rule_ids = end_tp.rule_ids + [rule.id] + start_tp.rule_ids
            # end_tp header = intersection(end_tp, rule, start_tp) 
            self.network_delete_rule(self.topology_graph.get_switch(r_end.get_switch_id()).modified_input_rules[r_end.id])
            self.network_delete_rule(self.topology_graph.get_switch(r_end.get_switch_id()).modified_output_rules[r_end.id])
            self.network_delete_rule(self.topology_graph.get_switch(r_end.get_switch_id()).sendback_rules[r_end.id])
            self.network_insert_rule(r_end)
            self.network_insert_rule(rule)
            #self.packetouts[index] should change the packet header
            self.packetouts[start_tp.index] = generate_packetout(self.testpackets[start_tp.index], self.datapaths, self.rules)
            for rule_id in end_tp.rule_ids:
                self.rules[rule_id].path_index = start_tp.index
            del self.packetouts[end_tp.index]
            del self.testpackets[end_tp.index]
            self.send_tpindex.remove(end_tp.index)
        elif start_tp is not None:
            if Detection.DEBUG_MSG: print '--------------------------2'
            rule.path_index = start_tp.index
            self.testpackets[start_tp.index].rule_ids = [rule.id] + start_tp.rule_ids
            self.network_insert_rule(rule)
            # start_tp header = intersection(rule, start_tp) 
            self.packetouts[start_tp.index] = generate_packetout(self.testpackets[start_tp.index], self.datapaths, self.rules)
            #self.packetouts[index] should change the packet header
        elif end_tp is not None:
            if Detection.DEBUG_MSG: print '--------------------------3'
            rule.path_index = end_tp.index
            self.testpackets[end_tp.index].rule_ids = end_tp.rule_ids + [rule.id]
            # end_tp header = intersection(end_tp, rule) 
            self.network_delete_rule(self.topology_graph.get_switch(r_end.get_switch_id()).modified_input_rules[r_end.id])
            self.network_delete_rule(self.topology_graph.get_switch(r_end.get_switch_id()).modified_output_rules[r_end.id])
            self.network_delete_rule(self.topology_graph.get_switch(r_end.get_switch_id()).sendback_rules[r_end.id])
            self.network_insert_rule(r_end)
            self.add_test_flow_entry(self.datapaths[to_dpid(rule.get_switch_id())], rule)
            #self.packetouts[index] should change the packet header
            self.header_tpindex[(rule.get_switch_id(), end_tp.get_header())] = end_tp.index
        else:
            if Detection.DEBUG_MSG: print '--------------------------4'
            index = self.inc_testpackets_size + Detection.INCREMENTAL_INDEX
            rule.path_index = index
            self.testpackets[index] = TestPacket(index, rule.get_prefix(), [rule.id])
            self.inc_testpackets_size += 1
            self.add_test_flow_entry(self.datapaths[to_dpid(rule.get_switch_id())], rule)
            self.packetouts[index] = generate_packetout(self.testpackets[index], self.datapaths, self.rules)
            self.header_tpindex[(rule.get_switch_id(), self.testpackets[index].get_header())] = index
            self.send_tpindex.add(index)

    def simulate_incremental_deleting(self):
        delays = []
        for rule_id in self.deleting_ruleid:
            rule = self.rules[rule_id]
            start_time = timeit.default_timer()
            self.simulate_deleting_rule(rule)
            #time.sleep(1)
            end_time = timeit.default_timer()
            delays.append(end_time - start_time)
        #print "Average delay of deleting one rule", (end_time - start_time) / float(len(self.deleting_ruleid))
        #print "PacketOut number", len(self.packetouts)
        #write_deleting_delay(Detection.FILENAME_PREFIX, delays)
        print 'Finish deleting rules'
        os._exit(1)

    def simulate_deleting_rule(self, rule):
        tp_index = rule.get_path_index()
        rule.is_deleted = True
        self.rules[rule.id].is_deleted = True

        deleted_number = 0
        for i, rule_id in enumerate(self.testpackets[tp_index].rule_ids):
            if self.rules[rule_id].is_deleted: 
                deleted_number += 1

        if len(self.testpackets[tp_index].rule_ids) - deleted_number == 0:
            self.network_delete_rule(rule)
            del self.testpackets[tp_index]
            del self.packetouts[tp_index]
            self.send_tpindex.remove(tp_index)
            return

        for i, rule_id in enumerate(self.testpackets[tp_index].rule_ids):
            if i == 0 and rule_id == rule.id:
                if Detection.DEBUG_MSG: print '--------------------------1'
                self.network_delete_rule(rule)
                self.testpackets[tp_index].rule_ids = self.testpackets[tp_index].rule_ids[1:]
                self.packetouts[tp_index] = generate_packetout(self.testpackets[tp_index], self.datapaths, self.rules)
                end_rule = self.rules[self.testpackets[tp_index].rule_ids[-1]]
                self.header_tpindex[(end_rule.get_switch_id(), self.testpackets[tp_index].get_header())] = tp_index
                return
            elif i == len(self.testpackets[tp_index].rule_ids)-1 and rule_id == rule.id:
                if Detection.DEBUG_MSG: print '--------------------------2'
                self.network_delete_rule(self.topology_graph.get_switch(rule.get_switch_id()).modified_input_rules[rule.id])
                self.network_delete_rule(self.topology_graph.get_switch(rule.get_switch_id()).modified_output_rules[rule.id])
                self.network_delete_rule(self.topology_graph.get_switch(rule.get_switch_id()).sendback_rules[rule.id])
                self.testpackets[tp_index].rule_ids = self.testpackets[tp_index].rule_ids[:-1]
                end_rule = self.rules[self.testpackets[tp_index].rule_ids[-1]]
                self.header_tpindex[(end_rule.get_switch_id(), self.testpackets[tp_index].get_header())] = tp_index
                self.add_test_flow_entry(self.datapaths[to_dpid(end_rule.get_switch_id())], end_rule)
                return
            if rule_id == rule.id:
                if Detection.DEBUG_MSG: print '--------------------------3'
                self.network_delete_rule(rule)
                datapath = self.datapaths[to_dpid(rule.get_switch_id())]
                ofproto = datapath.ofproto
                parser = datapath.ofproto_parser
                in_port = to_dpid(rule.get_in_port())
                ipv4_src = (rule.get_prefix()[:rule.get_prefix().index('/')], '255.255.255.0')
                tcp_src = self.testpackets[tp_index].get_unique_header()
                match = parser.OFPMatch(in_port=in_port, eth_type=0x800, ipv4_src=ipv4_src, ip_proto=inet.IPPROTO_TCP, tcp_src=tcp_src)
                self.add_flow(datapath, rule.get_priority(), match, [parser.OFPActionOutput(to_dpid(rule.get_out_port()), ofproto.OFPCML_NO_BUFFER)], table_id=rule.get_table_id())
                if Detection.DEBUG_MSG: print "Insert ", rule, rule.get_table_id()
                return

