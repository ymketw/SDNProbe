#ifndef TOPOLOGICAL_SORT
#define TOPOLOGICAL_SORT

#include <unordered_map>
#include <vector>
#include <queue>

#include "vertex.hpp"
#include "rule.hpp"

class TopologicalSort{
public:
	TopologicalSort(int vertex_number, std::unordered_map<int , Vertex> *ori_rule_graph, std::unordered_map<int, int> *rule_grpah_index_id);
	~TopologicalSort();

	void start(std::unordered_map<int , Vertex> *ori_rule_graph, std::unordered_map<int, int> *rule_grpah_index_id);
	std::vector<int>* getSortingList();
	std::unordered_map<int, Vertex>* getRuleGraph();

	void printSortingList();

private:
	int vertex_number;
	std::unordered_map<int, Vertex> rule_grpah;

	std::vector<int> sorting_list;
	std::unordered_map<int, int> indegree;
};

#endif
