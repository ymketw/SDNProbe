#ifndef HOPCROFT_KARP_H
#define HOPCROFT_KARP_H

#include <unordered_map>
#include <vector>
#include <boost/dynamic_bitset.hpp>
#include <queue>
#include <limits>

#include "vertex.hpp"
#include "rule.hpp"
#include "utils.hpp"

class HopcroftKarp{
public:
	HopcroftKarp(int vertex, std::unordered_map<int, Vertex> *rule_graph, std::unordered_map<int, int> *rule_graph_index_id, std::vector<int> *sorting_list);
	~HopcroftKarp();

	void start(std::unordered_map<int, Vertex> *rule_graph);
	std::unordered_map<int, int> *getMatchX();
	int getMatchingNumber();

	void printMatch();

private:
	bool BFS(std::unordered_map<int, Vertex> *rule_graph);
	bool DFS(std::unordered_map<int, Vertex> *rule_graph, int u);
	int vertex_number;
	int matching_number;
	std::vector<int> vertices;

	//std::unordered_map<int, int> init_visited;
	std::unordered_map<int, int> matchX;
	std::unordered_map<int, int> matchY;
	std::unordered_map<int, int> distance;
	std::unordered_map<int, boost::dynamic_bitset<> > rules;
};

#endif
