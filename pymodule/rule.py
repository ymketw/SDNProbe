import cPickle

def dump_rules(filename, rules):
    with open(filename, 'w') as f:
        cPickle.dump(rules, f, cPickle.HIGHEST_PROTOCOL)

def load_rules(filename):
    with open(filename, 'r') as f:
        rules = cPickle.load(f)
    return rules

class Rule():
    APPLY_ACTION = 0
    CLEAR_ACTION = 1
    WRITE_ACTION = 2
    GOTO_TABLE = 3
    INSTRUCTION = [APPLY_ACTION, CLEAR_ACTION, WRITE_ACTION, GOTO_TABLE]
    
    SET_FIELD = 0
    GROUP = 1
    OUTPUT = 2
    ACTION = [SET_FIELD, GROUP, OUTPUT]

    EDGE_PORT = 1000

    MAX_PRIORITY = 30000

    def __init__(self, id, switch_id, prefix, in_port, out_port, priority=MAX_PRIORITY):
        self.id = id;
        self.switch_id = switch_id;
        self.priority = priority 
        self.prefix = prefix
        self.header_space, self.ip, self.match_length = self.to_header_space(prefix)
        self.out_port = out_port
        self.in_port = in_port
        self.is_path_start = False
        self.is_path_end = False
        self.timeout = 0
        self.path_index = None

        self.inst_actions = {}
        self.table_id = 0
        self.group_id = None
        self.modify_field = None
        self.all_pair_path_index = None

        self.is_incremental = False
        self.is_sendback = False
        self.is_deleted = False
        self.is_modified_input = False
        self.is_modified_output = False

    def to_header_space(self, prefix):
        ip = prefix.split('/')[0]
        match_length = 32 if len(prefix.split('/')) < 2 else int(prefix.split('/')[1] )
        hs = ''.join([bin(int(x)+256)[3:] for x in ip.split('.')])

        hs = hs[:match_length] 
        hs += 'x'*(32-len(hs))

        return hs, ip, match_length

    def is_match(self, last_rule):
        return self.header_space[:self.header_space.index('x')] == last_rule.get_header_sapce()[:self.header_space.index('x')]

    def serialize(self):
        return cPickle.dumps(self)

    def get_id(self):
        return self.id

    def get_switch_id(self):
        return self.switch_id

    def set_in_port(self, in_port):
        self.in_port = in_port

    def get_in_port(self):
        return self.in_port

    def set_out_port(self, out_port):
        self.out_port = out_port

    def get_out_port(self):
        return self.out_port

    def set_inst_actions(self, inst, actions):
        self.inst_actions[inst] = actions

    def set_table_id(self, table_id):
        self.table_id = table_id

    def get_table_id(self):
        return self.table_id

    def set_path_index(self, index):
        self.path_index = index

    def get_path_index(self):
        return self.path_index

    def set_all_pair_path_index(self, index):
        self.all_pair_path_index = index;

    def set_priority(self, priority):
        self.priority = priority

    def get_priority(self):
        return self.priority

    def set_prefix(self, prefix):
        self.prefix = prefix
        self.header_space, self.ip, self.match_length = self.to_header_space(prefix)

    def get_prefix(self):
        return self.prefix

    def get_header_space(self):
        return self.header_space

    def get_all_pair_path_index(self):
        return self.all_pair_path_index;

    def __str__(self):
        string = 'Rule ID: ' + str(self.id) + ', ' + "Switch ID: " + str(self.switch_id) + ', ' + \
                'Priority: ' + str(self.priority) + ', ' + 'Prefix: ' + self.prefix + ', ' + 'HeaderSpace: ' + self.header_space + ', ' + \
                'Inport: ' + str(self.in_port) + ', ' + 'Outport: ' + str(self.out_port) + ', ' + 'Inst_actions: ' + str(self.inst_actions)
        return string


if __name__ == '__main__':
    pass

