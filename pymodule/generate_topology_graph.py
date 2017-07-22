#!/usr/bin/python

import argparse
import collections
import cPickle
from sets import Set

from topology import TopologyGraph
from switch import Switch
from rule import Rule, dump_rules, load_rules
from testpacket import TestPacket

import numpy
from graph_tool.all import *

def construct_edges(max_switch_ID):
    global index_nodes, adjacency_matrix, topology_graph
    for node in range(max_switch_ID+1):
        v = topology_graph.add_vertex()
        topology_graph.set_switch(v, node)

    edges_in_graph = Set()
    for index, row in enumerate(adjacency_matrix):
        for j, neighbor in enumerate(row):
            i = index_nodes[index] 
            if neighbor != -1 and i != j and (i, j) not in edges_in_graph and (j, i) not in edges_in_graph:
                topology_graph.add_edge(topology_graph.vertex(i), topology_graph.vertex(j))
                edges_in_graph.add((i, j))
                edges_in_graph.add((j, i))

    topology_graph.vertex_properties['exist'] = topology_graph.new_vertex_property('bool') 
    topology_graph.edge_properties['exist'] = topology_graph.new_edge_property('bool') 
    for v in topology_graph.vertices():
        topology_graph.vertex_properties['exist'][v] = True if int(v) in index_nodes.values() else False
    for e in topology_graph.edges():
        topology_graph.edge_properties['exist'][e] = True if e.source() in index_nodes.values() and e.target() in index_nodes.values() else False

    topology_graph.set_vertex_filter(topology_graph.vertex_properties['exist'])
    topology_graph.set_edge_filter(topology_graph.edge_properties['exist'])


def read_topology_file(input_name):
    global index_nodes, adjacency_matrix, topology_graph
    
    with open(input_name, 'r') as f:
        switch_number = int(f.readline().strip())
        rows = []
        max_switch_ID = 0
        for i in xrange(switch_number):
            row = f.readline().strip().split()
            rows.append(row)
            for ID in row:
                if int(ID) > max_switch_ID: max_switch_ID = int(ID)
            index_nodes[i] = int(row[0])

        for row in rows:
            adjacency_row = [-1] * (max_switch_ID+1)
            for i in row:
                adjacency_row[int(i)] = int(i)
            if adjacency_matrix == None:
                adjacency_matrix = numpy.array(adjacency_row)
            else:
                adjacency_matrix = numpy.vstack([adjacency_matrix, adjacency_row])

        construct_edges(max_switch_ID)

        for i in xrange(switch_number):
            switch_ID, rule_num = f.readline().strip().split()
            for j in xrange(int(rule_num)):
                rule_id, switch_id, prefix, headerspace, in_port, out_port, priority, path_index = f.readline().strip().split()
                rule = Rule(int(rule_id), int(switch_ID), prefix, int(in_port), int(out_port), int(priority))
                rule.set_path_index(int(path_index))
                
                topology_graph.get_switch(topology_graph.vertex(int(switch_ID))).add_flow_entry(rule.get_id(), rule)

def output_topology(filename):
    global topology_graph
    topology_graph.save(filename, fmt='graphml')
    #print 'vertices:', topology_graph.num_vertices()
    #print 'edges:', topology_graph.num_edges()
      

def print_topology(topology_graph):
    def print_rule(topology_graph, u):
        for rule_id, rule in topology_graph.get_switch(u).get_flow_table().iteritems():
            print rule
    
    for v in topology_graph.vertices():
        print 'src:', v, topology_graph.get_switch(v)
        for u in v.all_neighbours():
            print u, topology_graph.get_switch(u)
        print_rule(topology_graph, v)
        print
        print
    print [int(v) for v in topology_graph.vertices()]
            

def attach_testpackets_rules(input_filename, topology_graph, testpackets, rules):
    with open(input_filename, 'r') as f:
        contents = f.readlines()
        contents = [c.strip() for c in contents]
        line_num = 0
        path_number = int(contents[line_num])
        line_num += 1
        for i in xrange(path_number):
            path_info = contents[line_num].split()
            index = int(path_info[0])
            prefix = path_info[1]
            rule_num = int(path_info[2])
            rule_ids = path_info[3:]
            rule_ids = [int(r) for r in rule_ids]
            testpacket = TestPacket(index, prefix, rule_ids)
            ##testpackets.append(testpacket)
            testpackets[index] = testpacket
            line_num += 1
            #print testpacket

            for j in xrange(rule_num):
                rule_info = contents[line_num+j].split()
                rule_id = int(rule_info[0])
                switch_id = int(rule_info[1])
                ip = rule_info[2]
                in_port = int(rule_info[3])
                out_port = int(rule_info[4])
                priority = int(rule_info[5])
                rule = Rule(rule_id, switch_id, ip, in_port, out_port, priority=priority)
                rule.set_path_index(index)
                if j == 0:
                    rule.is_path_start = True
                if j == rule_num-1:
                    rule.is_path_end = True
                #print rule
                rules[rule_id] = rule
                topology_graph.get_switch(switch_id).add_flow_entry(rule_id, rule)

            line_num += rule_num

def dump_testpackets(filename, testpackets):
    with open(filename, 'w') as f:
        cPickle.dump(testpackets, f, cPickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-i', '--input', nargs=1, required=True, help='the filename of topology file.')

    input_name = argparser.parse_args().input[0]
    output_name = input_name
    output_name += '.graphml' if not output_name.endswith('.graphml') else ''
    
    index_nodes = collections.OrderedDict()
    adjacency_matrix = None
    topology_graph = TopologyGraph()
    topology_graph.set_directed(False)
    topology_graph.vertex_properties['switch'] = topology_graph.new_vertex_property('python::object')

    print 'Read "' + input_name + '"'
    print 'Read "' + input_name + '.testpackets"'
    read_topology_file(input_name)
    testpackets = {}
    rules = {}
    print 'Attach test packets on topology graph'
    attach_testpackets_rules(input_name+'.testpackets', topology_graph, testpackets, rules)
    dump_testpackets(input_name+'.testpackets.pkl', testpackets)
    dump_rules(input_name+'.rules.pkl', rules)

    output_topology(output_name)

    print 'Output: (1) ' + output_name
    print 'Output: (2) ' + input_name + '.testpackets.pkl'
    print 'Output: (3) ' + input_name + '.rules.pkl'
