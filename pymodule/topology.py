import sys
from graph_tool.all import *                                                                  

from switch import Switch
from rule import Rule

def load_topology(filename):
    topology_graph = load_graph(filename, fmt='graphml')
    topology_graph.set_vertex_filter(topology_graph.vertex_properties['exist'])
    topology_graph.set_edge_filter(topology_graph.edge_properties['exist'])
    topology_graph.__class__ = TopologyGraph

    print >> sys.stderr, 'switch number:', topology_graph.num_vertices()
    print >> sys.stderr, 'link number', topology_graph.num_edges()

    return  topology_graph


class TopologyGraph(Graph):
    def __init__(self):
        super(TopologyGraph, self).__init__()

    def set_switch(self, i, name):
        self.vertex_properties['switch'][i] = Switch(int(i), name)

    def get_switch(self, i):
        return self.vertex_properties['switch'][i]

    def add_flow_entry(self, i, rule, table_id=0):
        for next_rule in self.get_switch(rule.out_port).get_flow_table(table_id):
            if next_rule.is_match(rule) and match_count == 0:
                self.get_switch(i).add_flow_entry(rule, next_rule, table_id)
                return
        self.get_switch(i).add_flow_entry(rule, None, table_id)

    def delete_flow_entry(self, i):
        pass

    def is_vertex_exist(self, i):
        return self.vertex_properties['exist'][i]


if __name__ == '__main__':
    pass
