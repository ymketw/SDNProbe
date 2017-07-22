#!/usr/bin/python
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import RemoteController, Node

import sys
sys.path.append('pymodule/')
from graph_tool.all import *
from sets import Set

from topology import TopologyGraph
from topology import load_topology
from switch import Switch
from testpacket import *
from rule import *


class Link():
    def __init__(self, s1, s2, p1, p2):
        self.s1 = s1
        self.s2 = s2
        self.p1 = p1
        self.p2 = p2
    
    def __str__(self):
        return self.s1 + ' ' + self.s2 + ' ' + str(self.p1) + ' ' + str(self.p2)


class Topology(Topo):
    FILENAME = ''

    def switch_name(self, node):
        return 's' + str(int(node))
    
    def dpid(self, node):
        return format(int(node)+1, 'x').zfill(16)

    def to_dpid(self, switch_id):
        return switch_id + 1

    def add_neighbor_switch(self, src_node):
        for neighbor in src_node.all_neighbours():
            if neighbor not in self.switch_table:
                self.myswitches[int(neighbor)] = self.addSwitch(self.switch_name(neighbor), dpid=self.dpid(neighbor), protocols='OpenFlow13')
                self.switch_table.add(neighbor)

    def add_neighbor_link(self, src_node):
        for neighbor in src_node.all_neighbours():
            for v in neighbor.all_neighbours():
                if int(src_node) == int(v) and (self.switch_name(src_node), int(neighbor)) not in self.link_table and (self.switch_name(neighbor), int(src_node)) not in self.link_table:
                    self.addLink(self.switch_name(src_node), self.switch_name(neighbor), port1=int(neighbor)+1, port2=int(src_node)+1)
                    self.mylinks.append(Link(self.switch_name(src_node), self.switch_name(neighbor), int(neighbor), int(src_node)))
                    self.link_table[(self.switch_name(src_node), int(neighbor))] = (self.switch_name(neighbor), int(src_node))
                    self.link_table[(self.switch_name(neighbor), int(src_node))] = (self.switch_name(src_node), int(neighbor))

    def read_config(self, config_filename):
        with open(config_filename, 'r') as f:
            for line in f:
                var, val = line.strip().split('=') 
                if var == 'TOPOLOGY_FILE': Topology.FILENAME += val

    def __init__(self):
        Topo.__init__(self)

        self.read_config('config/config')
        self.topology_graph = load_topology(Topology.FILENAME+ '.graphml')
        
        self.link_table = {} 
        self.switch_table = Set() 

        self.mylinks = []
        self.myswitches = {}

        for v in self.topology_graph.vertices():
            #node_name = self.topology_graph.vertex_properties['name'][v]
            print 'switch id:', v, ' dpid: ', self.dpid(v)
            current_sw_name = self.switch_name(v)

            if v not in self.switch_table:
                self.myswitches[int(v)] = self.addSwitch(current_sw_name, dpid=self.dpid(v), protocols='OpenFlow13')
                self.switch_table.add(v)
            self.add_neighbor_switch(v)
            self.add_neighbor_link(v)


def write_mn_status(status):
    '''
    status == 0: open
    status == 1: close
    '''
    with open('mininet.status', 'w') as f:
        f.write(str(status))


if __name__ == '__main__':
    topos = {'topology':(lambda: Topology())}

    topo = Topology()
    net = Mininet(topo=topo, 
                    controller=lambda name: RemoteController(name, ip='127.0.0.1'),
                    listenPort=6633)
    
    net.start()
    #write_mn_status(1)
    CLI(net)
    net.stop()
    #write_mn_status(0)
