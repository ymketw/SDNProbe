#include "maximum_matching.hpp"

MaximumMatching::MaximumMatching(int vertex_number, std::unordered_map<int, Vertex> *rule_graph, std::unordered_map<int, int> *rule_graph_index_id, std::vector<int> *sorting_list){
	this->vertex_number = vertex_number;
	this->matching_number = 0;
	this->vertices.reserve(vertex_number);
	for ( int i = 0; i < vertex_number; i++ ){
		int rule_id = rule_graph_index_id->at(i);
		this->vertices.push_back(sorting_list->at(i));
		this->matchX[rule_id] = -1;
		this->matchY[rule_id] = -1;
		this->init_visited[rule_id] = 0;
		this->rules[rule_id] = rule_graph->at(rule_id).getRule()->getInHeaderSpace();
	}
}

MaximumMatching::~MaximumMatching(){
}

void MaximumMatching::start(std::unordered_map<int, Vertex> *rule_graph){
	for ( unsigned int i = 0; i < this->vertices.size(); i++ ){
		int u = this->vertices.at(i);
		if ( this->matchX[u] == -1 ){
			std::unordered_map<int, int> visited = init_visited;
			if ( DFS(rule_graph, &visited, u) ){
				this->matching_number++;
			}
		}
	}
}

bool MaximumMatching::DFS(std::unordered_map<int, Vertex> *rule_graph, std::unordered_map<int, int> *visited, int u){
	for ( unsigned int i = 0; i < rule_graph->at(u).getOutNeighbors()->size(); i++ ){
		int v = rule_graph->at(u).getOutNeighbors()->at(i);
		if ( visited->at(v) == 0 && is_match(this->rules[u], this->rules[v]) ){
			visited->at(v) = 1;
			if ( this->matchY[v] == -1 || this->DFS(rule_graph, visited, this->matchY[v]) ){
				this->matchX[u] = v;
				this->matchY[v] = u;
				this->rules[v] = intersection(rules[u], rules[v]);
				return true;
			}
		}
	}
	return false;
}	

std::unordered_map<int, int>* MaximumMatching::getMatchX(){
	return &this->matchX;
}

void MaximumMatching::printMatch(){
	for ( auto &k : this->matchX ){
		std::cout << k.first << " " << k.second << std::endl;
	}
}

int MaximumMatching::getMatchingNumber(){
	return this->matching_number;
}
