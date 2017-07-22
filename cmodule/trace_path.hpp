#ifndef TRACE_PATH_H
#define TRACE_PATH_H

#include <iostream>
#include <vector>
#include <unordered_map>
#include <algorithm> 

class TracePath{
public:
	TracePath(int vertex_number, std::unordered_map<int, int> *rule_graph_index_id);
	~TracePath();

	void start(std::unordered_map<int, int> *match, std::unordered_map<int, std::unordered_map<int, int> > *P, std::vector<int> *sorting_vertices);
	void print();

	std::vector<std::vector<int> >* getAllPaths();

private:
	int vertex_number;

	std::vector<std::vector<int> > all_paths;
	std::unordered_map<int, int> visited;
};

#endif
