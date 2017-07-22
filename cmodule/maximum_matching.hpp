#ifndef MAXIMUM_MATCHING_H
#define MAXIMUM_MATCHING_H

#include <unordered_map>
#include <vector>
#include <boost/dynamic_bitset.hpp>

#include "vertex.hpp"
#include "rule.hpp"
#include "utils.hpp"

class MaximumMatching{
public:
	MaximumMatching(int vertex, std::unordered_map<int, Vertex> *rule_graph, std::unordered_map<int, int> *rule_graph_index_id, std::vector<int> *sorting_list);
	~MaximumMatching();

	void start(std::unordered_map<int, Vertex> *rule_graph);
	std::unordered_map<int, int> *getMatchX();
	int getMatchingNumber();

	void printMatch();

private:
	bool DFS(std::unordered_map<int, Vertex> *rule_graph, std::unordered_map<int, int> *visited, int u);
	int vertex_number;
	int matching_number;
	std::vector<int> vertices;

	std::unordered_map<int, int> init_visited;
	std::unordered_map<int, int> matchX;
	std::unordered_map<int, int> matchY;
	std::unordered_map<int, boost::dynamic_bitset<> > rules;
};

#endif
