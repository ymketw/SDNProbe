import copy

class Switch():
    MAX_TABLE_ID = 2
    def __init__(self, id, name):
        self.name = name
        self.id = id
        self.dpid = id+1
        self.flow_table = []
        for i in xrange(self.MAX_TABLE_ID):
            self.flow_table.append({})
        self.incremental_rules = {}
        self.modified_input_rules = {}
        self.modified_output_rules = {}
        self.sendback_rules = {}
        self.deleted_rules = {}

    def get_id(self):
        return self.id

    def get_dpid(self):
        return self.dpid

    def add_flow_entry(self, rule_id, rule, table_id=0):
        self.flow_table[table_id][rule_id] = rule

    def modify_flow_entry(self):
        pass

    def delete_flow_entry(self, rule_id, table_id=0):
        del self.flow_table[table_id][rule_id]

    def get_flow_table(self, table_id=0):
        return self.flow_table[table_id]

    def get_name(self):
        return self.name

    def get_rule_number(self, table_id=0):
        return len(self.flow_table[table_id])

    def add_incremental_rule(self, rule):
        self.incremental_rules[rule.id] = rule

    def add_modified_input_rule(self, rule):
        self.modified_input_rules[rule.id] = rule

    def add_modified_output_rule(self, rule):
        self.modified_output_rules[rule.id] = rule

    def add_sendback_rule(self, rule):
        self.sendback_rules[rule.id] = rule

    def add_deleted_rule(self, rule):
        self.deleted_rules[rule.id] = rule

    def __str__(self):
        return str(self.name)


if __name__ == '__main__':
    pass
