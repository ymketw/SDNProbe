#include "switch.hpp"

Switch::Switch(){

}

Switch::Switch(int index, int id){
	this->index = index;
	this->id = id;
	this->neighbors.reserve(32);
	this->rules.reserve(4096);
}

Switch::~Switch(){
}

void Switch::addNeighbor(int neighbor_id){
	this->neighbors.push_back(neighbor_id);
}

void Switch::addRule(int rule_id){
	this->rules.push_back(rule_id);
}

int Switch::getID(){
	return this->id;
}

int Switch::getIndex(){
	return this->index;
}

int Switch::getNeighborsSize(){
	return this->neighbors.size();
}

std::vector<int>* Switch::getNeighbors(){
	return &this->neighbors;
}

int Switch::getRulesSize(){
	return this->rules.size();
}

std::vector<int>* Switch::getRules(){
	return &this->rules;
}
