#ifndef SWITCH_H
#define SWITCH_H

#include <unordered_map>
#include <vector>

#include "rule.hpp"

class Switch{
public:
	Switch();
	Switch(int index, int id);
	~Switch();

	void addNeighbor(int neighbor_id);
	void addRule(int rule_id);

	int getID();
	int getIndex();
	int getNeighborsSize();
	std::vector<int>* getNeighbors();
	int getRulesSize();
	std::vector<int>* getRules();

private:
	int id;
	int index;
	std::vector<int> neighbors;
	std::vector<int> rules;
};

#endif
