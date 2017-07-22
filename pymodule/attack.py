from ryu.ofproto import ether, inet
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, tcp, vlan, mpls

import sys 
import time
import cPickle
import copy
import random
from array import array

from graph_tool.all import *
from topology import *
from testpacket import *
from switch import *
from rule import *

def initialize_persistent_fault(persistent_num, rules, testpackets):
    random.seed()
    switch_ids = set()
    persistent_fault = set()
    while len(persistent_fault) < persistent_num:
        tp = testpackets[random.randint(0, len(testpackets)-1)]
        rule_id = tp.rule_ids[random.randint(0, len(tp.rule_ids)-1)]
        rule = rules[rule_id]
        #if rule.get_switch_id() not in switch_ids:
        #    switch_ids.add(rule.get_switch_id())
        persistent_fault.add(rule_id)
    return persistent_fault

def initialize_nonpersistent_fault(nonpersistent_num, rules, testpackets, persistent_fault):
    random.seed()
    switch_ids = set()
    nonpersistent_fault = set()
    while len(nonpersistent_fault) < nonpersistent_num:
        tp = testpackets[random.randint(0, len(testpackets)-1)]
        rule_id = tp.rule_ids[random.randint(0, len(tp.rule_ids)-1)]
        rule = rules[rule_id]
        if rule.get_switch_id() not in switch_ids and rule_id not in persistent_fault:
            switch_ids.add(rule.get_switch_id())
            nonpersistent_fault.add(rule_id)
    return nonpersistent_fault

