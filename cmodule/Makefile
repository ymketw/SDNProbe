GCC=g++
CPPFLAGS=-std=c++11 -o3 -fopenmp
OBJS=generate_test_packets.o switch.o rule.o vertex.o utils.o topological_sort.o transitive_closure.o maximum_matching.o trace_path.o test_packet.o hopcroft_karp.o

all: generate_test_packets 

generate_test_packets: $(OBJS)
	$(GCC) $(CPPFLAGS) $(OBJS) -o generate_test_packets

generate_test_packets.o: generate_test_packets.cpp
	$(GCC) $(CPPFLAGS) -c generate_test_packets.cpp -o generate_test_packets.o

switch.o: switch.cpp
	$(GCC) $(CPPFLAGS) -c switch.cpp -o switch.o

rule.o: rule.cpp
	$(GCC) $(CPPFLAGS) -c rule.cpp -o rule.o

vertex.o: vertex.cpp
	$(GCC) $(CPPFLAGS) -c vertex.cpp -o vertex.o

utils.o: utils.cpp
	$(GCC) $(CPPFLAGS) -c utils.cpp -o utils.o

topological_sort.o: topological_sort.cpp
	$(GCC) $(CPPFLAGS) -c topological_sort.cpp -o topological_sort.o

transitive_closure.o: transitive_closure.cpp
	$(GCC) $(CPPFLAGS) -c transitive_closure.cpp -o transitive_closure.o

maximum_matching.o: maximum_matching.cpp
	$(GCC) $(CPPFLAGS) -c maximum_matching.cpp -o maximum_matching.o

trace_path.o: trace_path.cpp
	$(GCC) $(CPPFLAGS) -c trace_path.cpp -o trace_path.o

test_packet.o: test_packet.cpp
	$(GCC) $(CPPFLAGS) -c test_packet.cpp -o test_packet.o

hopcroft_karp.o: hopcroft_karp.cpp
	$(GCC) $(CPPFLAGS) -c hopcroft_karp.cpp -o hopcroft_karp.o

clean:
	rm -rf *.o generate_test_packets

