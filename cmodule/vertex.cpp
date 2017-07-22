#include "vertex.hpp"

Vertex::Vertex(){
}

Vertex::Vertex(Rule *rule){
	this->rule = rule;
	this->in_neighbors.reserve(1024);
	this->out_neighbors.reserve(1024);
}

Vertex::Vertex(Vertex *vertex){
	this->rule = vertex->getRule();
	this->in_neighbors.reserve(vertex->getInNeighbors()->size());
	this->out_neighbors.reserve(vertex->getOutNeighbors()->size());
	for ( unsigned int i = 0; i < vertex->getInNeighbors()->size(); i++ ){
		this->in_neighbors.push_back(vertex->getInNeighbors()->at(i));
	}
	for ( unsigned int i = 0; i < vertex->getOutNeighbors()->size(); i++ ){
		this->out_neighbors.push_back(vertex->getOutNeighbors()->at(i));
	}
}

Vertex::~Vertex(){
}

//int Vertex::getIndex(){
//	return this->index;
//}

int Vertex::getID(){
	return this->rule->getID();
}

Rule* Vertex::getRule(){
	return this->rule;
}

std::vector<int>* Vertex::getInNeighbors(){
	return &this->in_neighbors;
}

std::vector<int>* Vertex::getOutNeighbors(){
	return &this->out_neighbors;
}

void Vertex::addInNeighbor(int neighbor_id){
	this->in_neighbors.push_back(neighbor_id);
}

void Vertex::addOutNeighbor(int neighbor_id){
	this->out_neighbors.push_back(neighbor_id);
}

void Vertex::print(){
	std::cout << "Rule id: " << this->rule->getID() << std::endl;
	std::cout << "In neighobrs: ";
	for ( unsigned int i = 0; i < this->in_neighbors.size(); i++ ){
		std::cout << this->in_neighbors[i] << " ";
	}
	std::cout << std::endl;
	std::cout << "Out neighobrs: ";
	for ( unsigned int i = 0; i < this->out_neighbors.size(); i++ ){
		std::cout << this->out_neighbors[i] << " ";
	}
	std::cout << std::endl;
}
