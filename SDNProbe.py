#!/usr/bin/python

from subprocess import Popen, PIPE, call

from interface import Interface


if __name__ == '__main__':
    CONFIG_FILENAME = 'config/config'

    interface = Interface(CONFIG_FILENAME)
    interface.read_config()
    
    while True:
        choice = interface.show_menu()
        if choice == 1:
            interface.show_config()
        elif choice == 2:
            interface.generate_test_packets()
        elif choice == 3:
            interface.generate_topology_graph()    
        elif choice == 4:
            interface.start_probing()
        elif choice == 5:
            interface.show_exit()
            exit()
