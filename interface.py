import os
import sys
import tty, termios
import collections
from subprocess import Popen, PIPE, call
from blessings import Terminal

class Interface:

    def __init__(self, config_filename):
        self.config_filename = config_filename
        self.config = collections.OrderedDict()
        self.term = Terminal()

        self.hline = u'\u2500'
        self.left_up = u'\u250c'
        self.right_up = u'\u2510'
        self.left_down = u'\u2514'
        self.right_down = u'\u2518'
        self.left_middle = u'\u251c'
        self.right_middle = u'\u2524'
        self.vline = u'\u2502'

        self.TITLE = ['SDNProbe: A Lightweight Tool for Securing SDN Data Plane with Active Probing'.center(self.term.width-2)]
        self.MENU = ['Show the configure file',
                     'Generate test packets from topology file',
                     'Generate topology graph for the controller as input',
                     'Start probing', 
                     'Exit (or press q)']
        self.menu_pos = 0


    def show_menu(self):
        while True:
            os.system('clear')
            
            print self.left_up + self.hline * (self.term.width-2) + self.right_up
            print self.vline + self.term.bold_cyan(self.TITLE[0]) + self.vline
            print self.left_middle + self.hline * (self.term.width-2) + self.right_middle


            for i, menu in enumerate(self.MENU):
                if i == self.menu_pos:
                    print self.vline + ' ' + self.term.yellow_reverse('[' + str(i+1) + '] ' + menu) + ' '*(self.term.width-len(menu)-7) + self.vline
                else:
                    print self.vline + ' ' + '[' + str(i+1) + '] ' + menu  + ' '*(self.term.width-len(menu)-7) + self.vline
            print self.left_down + self.hline * (self.term.width-2) + self.right_down
            print

            press = self.getch()
            if press == 'up': self.menu_pos = (self.menu_pos-1) % (len(self.MENU))
            elif press == 'down': self.menu_pos = (self.menu_pos+1) % (len(self.MENU))
            elif press == 'exit': return 5
            elif press == 'enter': return self.menu_pos+1


    def read_config(self):
        try:
            with open(self.config_filename, 'r') as f:
                for line in f:
                    var, val = line.strip().split('=')
                    self.config[var] = val
        except IOError:
            self.print_IOError(self.config_filename)
            exit()
        except:
            print self.term.bold_red('[-] Error')
            exit()

    def show_config(self):
        max_var_len = len(max(self.config.keys(), key=len))
        max_val_len = len(max(self.config.values(), key=len))
        width = max_var_len + 3 + max_val_len + 1

        print self.term.bold_green(' [+] Config file: ' + self.config_filename)
        print ' ' + self.left_up + self.hline * width + self.right_up
        for var, val in self.config.iteritems():
            print ' ' + self.vline + ' ' + var.ljust(max_var_len) + ' = ' + val.ljust(max_val_len) + self.vline
        print ' ' + self.left_down + self.hline * width + self.right_down

        self.check_config()

        self.show_coninue()

    def generate_test_packets(self):
        print self.term.bold_green(' [+] Generating test packets from "' + self.config['TOPOLOGY_FILE'] + '"')
        if not self.check_config(): 
            self.show_coninue()
            return False
        print

        p = Popen(['make', '-C', 'cmodule/'], stdout=PIPE)
        print self.term.bold_green(' [+] Make file')
        for line in iter(p.stdout.readline, b''):
            print self.term.bold_magenta(' ' * 5 + line.strip())
        print

        p = Popen(['cmodule/./generate_test_packets', self.config['TOPOLOGY_FILE']], stdout=PIPE)
        print self.term.bold_green(' [+] Start to generate test packets')
        for line in iter(p.stdout.readline, b''):
            if line.startswith('  '):
                print self.term.bold_magenta(' ' * 5 + line.strip())
            elif line.strip() == '': pass
            else:
                print self.term.bold_green(' [+] ' + line.strip())

        self.show_coninue()
    
    def generate_topology_graph(self):
        print self.term.bold_green(' [+] Generating topology graph from "' + self.config['TOPOLOGY_FILE'] + '" and "' + self.config['TOPOLOGY_FILE']  + '.testpackets"')
        if not self.check_config(): 
            self.show_coninue()
            return False
        p = Popen(['pymodule/generate_topology_graph.py', '-i', self.config['TOPOLOGY_FILE']], stdout=PIPE)
        for line in iter(p.stdout.readline, b''):
            print self.term.bold_green(' [+] ' + line.rstrip())

        self.show_coninue()

    def start_probing(self):
        p = Popen(['ryu-manager', 'pymodule/controller.py'], stdout=PIPE, stderr=PIPE)
        for line in iter(p.stderr.readline, b''):
            try:
                if line.startswith('---'): print self.term.bold_magenta(' [+] ' + line.strip())
                elif line.startswith('  '):
                    print self.term.bold_magenta(' ' * 5 + line.strip())
                else: print self.term.bold_green(' [+] ' + line.strip())
            except:
                pass
        print

        self.show_coninue()


    def show_exit(self):
        print self.term.bold_red(' [+] Exit...\n')

    def show_coninue(self):
        print 
        print self.term.bold_green(' [+] Press any key to continue...')
        self.getch()

    def check_config(self):
        if not os.path.exists(self.config['TOPOLOGY_FILE']):
            self.print_IOError(self.config['TOPOLOGY_FILE'])
            return False
        return True

    def print_IOError(self, filename):
        print self.term.bold_red(' [-] IOError: No such file: ' + filename)

    def getch(self):
        def input_key():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            key = ''
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                if ord(ch) == 13: return 'enter'
                elif ord(ch) == 113 or ord(ch) == 81: return 'exit'
                elif ord(ch) != 27: return False
                
                ch = sys.stdin.read(1)
                if ord(ch) != 91: return False
                
                ch = sys.stdin.read(1)
                if ord(ch) == 65: return 'up'
                elif ord(ch) == 66: return 'down'
                #elif ord(ch) == 67: return 'right'
                #elif ord(ch) == 68: return 'left'
                else: return False
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        while True:
            press_key = input_key()
            if press_key != '': break
        
        return press_key


