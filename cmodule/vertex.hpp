#ifndef VERTEX_H
#define VERTEX_H

#include <iostream>
#include <vector>

#include "rule.hpp"

class Vertex{
public:
	Vertex();
	Vertex(Rule *rule);
	Vertex(Vertex *vertex);
	~Vertex();

	int getID();
	Rule* getRule();
	std::vector<int>* getInNeighbors();
	std::vector<int>* getOutNeighbors();

	void addInNeighbor(int neighbor_id);
	void addOutNeighbor(int neighbor_id);

	void print();

private:
	Rule *rule;
	std::vector<int> in_neighbors;
	std::vector<int> out_neighbors;
};

#endif
