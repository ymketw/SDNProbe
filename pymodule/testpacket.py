import cPickle

def load_testpackets(filename):
    with open(filename, 'r') as f:
        testpackets = cPickle.load(f)
    return testpackets

class TestPacket():

    def __init__(self, index, prefix, rule_ids):
        self.index = index
        self.prefix = prefix
        self.header = prefix[:prefix.index('/')] if prefix.find('/') != -1 else prefix
        self.rule_ids = rule_ids
        self.unique_header = index

    def get_prefix(self):
        return self.prefix

    def get_header(self):
        return self.header

    def get_unique_header(self):
        return self.unique_header

    def __str__(self):
        string = str(self.index) + ' ' + str(self.prefix) + ' ' + str(self.header) + ' '
        for r in self.rule_ids:
            string += str(r) + ' '
        return string

if __name__ == '__main__':
    pass
