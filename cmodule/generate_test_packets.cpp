#include <iostream>
#include <fstream>
#include <sstream>

#include <vector>
#include <unordered_map>
#include <tuple>
#include <string>
#include <boost/dynamic_bitset.hpp>

#include <chrono>
#include <time.h>
#include <omp.h>

#include "vertex.hpp"
#include "rule.hpp"
#include "switch.hpp"

#include "topological_sort.hpp"
#include "transitive_closure.hpp"
#include "maximum_matching.hpp"
#include "trace_path.hpp"
#include "test_packet.hpp"
#include "hopcroft_karp.hpp"

#include "utils.hpp"

#define DEBUG false
#define DEBUG_TEST 2

void construct_rule_graph(std::unordered_map<int, Vertex> *rule_graph, int switch_number, std::unordered_map<int, int> *switch_index_id,
							std::unordered_map<int, Switch> *switches, std::unordered_map<int, Rule> *rules){
	int match_count = 0;
	#pragma omp parallel for
	for ( int u = 0; u < switch_number; u ++ ){
		Switch *s1 = &switches->at(switch_index_id->at(u));
		for ( int i = 0; i < s1->getNeighborsSize(); i++ ){
			Switch *s2 = &switches->at(s1->getNeighbors()->at(i));
			for ( int j = 0; j < s1->getRulesSize(); j++  ){
				Rule *r1 = &rules->at(s1->getRules()->at(j));
				if ( r1->getOutPort() != s2->getID() ) continue;
				for ( int k = 0; k < s2->getRulesSize(); k++ ){
					Rule *r2 = &rules->at(s2->getRules()->at(k));
					if ( r2->getInPort() != s1->getID() || !is_match(r1->getOutHeaderSpace(), r2->getInHeaderSpace()) ) continue;
					(&rule_graph->at(r1->getID()))->addOutNeighbor(r2->getID());
					(&rule_graph->at(r2->getID()))->addInNeighbor(r1->getID());
					match_count++;
				}
			}
		}
	}
}

void construct_rule_graph(int vertex_number, std::unordered_map<int, Vertex> *rule_graph, 
							std::unordered_map<int, int> *rule_graph_index_id, std::unordered_map<int, Rule> *rules){
	int match_count = 0;
	#pragma omp parallel for
	for ( int i = 0; i < vertex_number; i++ ){
		for ( int j = 0; j < vertex_number; j++ ){
			if ( i == j ) continue;
			Rule *r1 = &rules->at(rule_graph_index_id->at(i));
			Rule *r2 = &rules->at(rule_graph_index_id->at(j));
			if ( r1->getOutPort() == r2->getSwitchID() && r2->getInPort() == r1->getSwitchID() && is_match(r1->getOutHeaderSpace(), r2->getInHeaderSpace()) ){
				(&rule_graph->at(r1->getID()))->addOutNeighbor(r2->getID());
				(&rule_graph->at(r2->getID()))->addInNeighbor(r1->getID());
				match_count++;
			}
		}
	}
}

void print_rule_graph(int vertex_number, std::unordered_map<int, int> *rule_graph_index_id, std::unordered_map<int, Vertex> *rule_graph){
	for ( int i = 0; i < vertex_number; i++ ){
		int rule_id = rule_graph_index_id->at(i);
		rule_graph->at(rule_id).getRule()->print();
		rule_graph->at(rule_id).print();
	}
}

bool debug_test(std::vector<int> *path_indices, int path_index){
	if ( path_indices->size() < DEBUG_TEST ){
		path_indices->push_back(path_index);
		return true;
	}
	bool is_exist = false;
	for ( unsigned int i = 0; i < path_indices->size(); i++ ){
		if ( path_indices->at(i) == path_index ){
			is_exist = true;
		}
	}
	return is_exist;
}


void output_testpackests(std::string output_filename, std::vector<TestPacket> *test_packets, std::unordered_map<int, Rule> *rules){
	std::ofstream outfile(output_filename);
	outfile << test_packets->size() << std::endl;
	for ( unsigned int i = 0; i < test_packets->size(); i++ ){
		outfile << test_packets->at(i).getIndex() << " ";
		outfile << test_packets->at(i).getPrefix() << " ";
		outfile << test_packets->at(i).getPath()->size() << " ";
		for ( auto &rule_id : *test_packets->at(i).getPath() ){
			outfile << rule_id << " ";
		}
		outfile << std::endl;
		for ( auto &rule_id : *test_packets->at(i).getPath() ){
			outfile << rules->at(rule_id).getID() << " ";
			outfile << rules->at(rule_id).getSwitchID() << " ";
			outfile << rules->at(rule_id).getPrefix() << " ";
			outfile << rules->at(rule_id).getInPort() << " ";
			outfile << rules->at(rule_id).getOutPort() << " ";
			outfile << rules->at(rule_id).getPriority() << " ";
			outfile << std::endl;
		}
	}
}



int main(int argc, char *argv[]){
	std::string filename_prefix;
	std::string input_filename; 
	std::string output_filename;
	if ( argc == 2 ){
		input_filename = std::string(argv[1]);
		output_filename = input_filename + ".testpackets";
	}
	else{
		std::cout << "Wrong parameters" << std::endl;
		return 0;
	}
	
	//std::cout << filename_prefix << " " << input_filename << " " << output_filename << std::endl;

	std::ifstream infile(input_filename);

	std::unordered_map<int, int> rule_graph_index_id;
	std::unordered_map<int, int> switch_index_id;
	std::unordered_map<int, Switch> switches;
	std::unordered_map<int, Rule> rules;
	std::unordered_map<int, Vertex> rule_graph;
	rule_graph.reserve(1024000);

	std::vector<int> path_indices; //for test

	int switch_number;
	int vertex_number = 0;
	infile >> switch_number;
	switch_index_id.reserve(switch_number);
	//std::cout << switch_number << std::endl;

	for ( int i = 0; i < switch_number; i++ ){
		std::string line;
		int switch_id, neighbor_id;
		infile >> switch_id;
		Switch s(i, switch_id);
		std::getline(infile, line);
		std::stringstream ss(line);
		while ( ss >> neighbor_id ){
			s.addNeighbor(neighbor_id);
		}
		switches[switch_id] = s;
		switch_index_id[i] = switch_id;
	}

	for ( int i = 0; i < switch_number; i++ ){
		std::string line;
		int switch_id, rule_number;
		infile >> switch_id >> rule_number;
		//std::cout << switch_id << " " << rule_number << std::endl;
		std::getline(infile, line);
		for ( int j = 0; j < rule_number; j++ ){
			std::getline(infile, line);
			std::istringstream iss(line);
			int rule_id, in_port, out_port, priority, path_index;
			std::string header, prefix;
			iss >> rule_id >> switch_id >> prefix >> header >> in_port >> out_port >> priority >> path_index;
			//std::cout << rule_id << " " << switch_id << " " << prefix << " " << header << " " << in_port << " " << out_port << std::endl;
			if ( DEBUG && !debug_test(&path_indices, path_index) ) continue;
			rules[rule_id] = Rule(rule_id, switch_id, prefix, header, in_port, out_port, priority, path_index);

			rule_graph[rule_id] = Vertex(&rules[rule_id]);

			rule_graph_index_id[vertex_number] = rule_id;
			switches[switch_id].addRule(rule_id);
			vertex_number++;
		}
	}



	//for ( int i = 0; i < switch_number; i++ ){
	//	std::cout << switches[switch_index_id[i]].getID() << std::endl;
	//}
	auto start_time2 =std::chrono::high_resolution_clock::now();
	
	//Construct rulegraph
	std::cout << "Constructing Rule Graph" << std::endl;
	construct_rule_graph(&rule_graph, switch_number, &switch_index_id, &switches, &rules);

	std::cout << "  Rule number: " << vertex_number << std::endl;
	std::cout << std::endl;

	//Topological sorting
	auto start_time = std::chrono::high_resolution_clock::now();
	std::cout << "Topological Sorting" << std::endl;
	
	TopologicalSort topological_sort(vertex_number, &rule_graph, &rule_graph_index_id);
	topological_sort.start(&rule_graph, &rule_graph_index_id);
	std::cout << std::endl;


	//Transitive closure
	std::cout << "Transitive Closure" << std::endl;

	TransitiveClosure transitive_closure(vertex_number, topological_sort.getRuleGraph(), &rule_graph_index_id);
	transitive_closure.start(topological_sort.getRuleGraph(), &rule_graph_index_id);
	std::cout << std::endl;
	
	//Matching
	std::cout << "Maximum Matching" << std::endl;
	HopcroftKarp maximum_matching(vertex_number, transitive_closure.getRuleGraph(), &rule_graph_index_id, topological_sort.getSortingList());
	maximum_matching.start(transitive_closure.getRuleGraph());
	std::cout << "  Maximum matching number: " << maximum_matching.getMatchingNumber() << std::endl;
	//std::cout << "Path number: " << vertex_number - maximum_matching.getMatchingNumber() << std::endl;
	std::cout << std::endl;

	//Trace Path
	std::cout << "Trace Path" << std::endl;
	TracePath trace_path(vertex_number, &rule_graph_index_id);
	trace_path.start(maximum_matching.getMatchX(), transitive_closure.getP(), topological_sort.getSortingList());

	std::cout << "  Path number: " << trace_path.getAllPaths()->size() << std::endl;
	std::cout << std::endl;

	std::vector<TestPacket> test_packets;
	test_packets.reserve(trace_path.getAllPaths()->size());
	for ( unsigned int i = 0; i < trace_path.getAllPaths()->size(); i++ ){
		TestPacket packet(i, trace_path.getAllPaths()->at(i), &rules);
		test_packets.push_back(packet);
	}


	//Output testpackets
	//
	//
	std::cout << "Output test packets" << std::endl;
	output_testpackests(output_filename, &test_packets, &rules);
	std::cout << "  Test packet number: " << test_packets.size() << std::endl;

	
	auto end_time = std::chrono::high_resolution_clock::now();
	std::chrono::duration<double, std::milli> diff = end_time - start_time;
	std::chrono::duration<double, std::milli> diff2 = end_time - start_time2;
	std::cout << "  Test packet generation time including construct rule graph (sec): ";
	std::cout << (float)diff2.count() / 1000.0 << std::endl;
	std::cout << "  Test packet generation time (sec): " << (float)diff.count() / 1000.0 << std::endl;
	
	std::cout << "Output filename is: " << output_filename << std::endl;
	return 0;
}
