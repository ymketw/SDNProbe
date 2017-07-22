#ifndef TRANSITIVE_CLOSURE_H
#define TRANSITIVE_CLOSURE_H

#include <unordered_map>
#include <vector>
#include <queue>
#include <boost/dynamic_bitset.hpp>

#include "vertex.hpp"
#include "rule.hpp"

#include "utils.hpp"

class TransitiveClosure{
public:
	TransitiveClosure(int vertex_number, std::unordered_map<int, Vertex> *ori_rule_graph, std::unordered_map<int, int> *rule_graph_index_id);
	~TransitiveClosure();

	void start(std::unordered_map<int, Vertex> *ori_rule_graph, std::unordered_map<int, int> *rule_graph_index_id);
	std::unordered_map<int, Vertex>* getRuleGraph();
	std::unordered_map<int, std::unordered_map<int, int> > *getP();

private:
	void BFS(std::unordered_map<int, Vertex> *ori_rule_graph, int u);

	int vertex_number;
	std::unordered_map<int, Vertex> rule_graph;
	std::unordered_map<int, std::unordered_map<int, int> > P;
	std::unordered_map<int, boost::dynamic_bitset<> > rules;
};

#endif
