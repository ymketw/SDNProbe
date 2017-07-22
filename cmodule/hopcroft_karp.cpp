#include "hopcroft_karp.hpp"

HopcroftKarp::HopcroftKarp(int vertex_number, std::unordered_map<int, Vertex> *rule_graph, std::unordered_map<int, int> *rule_graph_index_id, std::vector<int> *sorting_list){
	this->vertex_number = vertex_number;
	this->matching_number = 0;
	this->vertices.reserve(vertex_number);
	for ( int i = 0; i < vertex_number; i++ ){
		int rule_id = rule_graph_index_id->at(i);
		this->vertices.push_back(sorting_list->at(i));
		this->matchX[rule_id] = -1;
		this->matchY[rule_id] = -1;
		this->rules[rule_id] = rule_graph->at(rule_id).getRule()->getInHeaderSpace();
	}
}

HopcroftKarp::~HopcroftKarp(){
}


void HopcroftKarp::start(std::unordered_map<int, Vertex> *rule_graph){
	while( this->BFS(rule_graph) ){
		for ( unsigned int i = 0; i < this->vertices.size(); i++ ){
			int u = this->vertices.at(i);
			if ( this->matchX[u] == -1 ){
				if ( DFS(rule_graph, u) ){
					this->matching_number++;
				}
			}
		}
	}
}

bool HopcroftKarp::BFS(std::unordered_map<int, Vertex> *rule_graph){
	std::queue<int> vertex_queue;
	for ( unsigned int i = 0; i < this->vertices.size(); i++ ){
		int u = this->vertices.at(i);
		if ( this->matchX[u] == -1 ){
			this->distance[u] = 0;
			vertex_queue.push(u);
		}
		else{
			this->distance[u] = std::numeric_limits<int>::max();
		}
	}
	this->distance[-1] = std::numeric_limits<int>::max();
	while ( !vertex_queue.empty() ){
		int u = vertex_queue.front();
		vertex_queue.pop();
		if ( this->distance[u] < this->distance[-1] ){
			for ( unsigned int i = 0; i < rule_graph->at(u).getOutNeighbors()->size(); i++  ){
				int v = rule_graph->at(u).getOutNeighbors()->at(i);	
				if ( this->distance[this->matchY[v]] == std::numeric_limits<int>::max() && is_match(this->rules[u], this->rules[v]) ){
					this->distance[this->matchY[v]] = this->distance[u] + 1;
					vertex_queue.push(this->matchY[v]);
				}
			}		
		}
	}
	return (this->distance[-1] != std::numeric_limits<int>::max());
}

bool HopcroftKarp::DFS(std::unordered_map<int, Vertex> *rule_graph, int u){
	if ( u != -1 ){
		for ( unsigned int i = 0; i < rule_graph->at(u).getOutNeighbors()->size(); i++ ){
			int v = rule_graph->at(u).getOutNeighbors()->at(i);
			if ( this->distance[matchY[v]] == this->distance[u] + 1 && is_match(this->rules[u], this->rules[v])){
				if ( DFS(rule_graph, matchY[v]) ){
					this->matchX[u] = v;
					this->matchY[v] = u;
					this->rules[v] = intersection(rules[u], rules[v]);
					return true;
				}
			}
		}
		this->distance[u] = std::numeric_limits<int>::max();
		return false;
	}
   return true;	
}	

std::unordered_map<int, int>* HopcroftKarp::getMatchX(){
	return &this->matchX;
}

void HopcroftKarp::printMatch(){
	for ( auto &k : this->matchX ){
		std::cout << k.first << " " << k.second << std::endl;
	}
}

int HopcroftKarp::getMatchingNumber(){
	return this->matching_number;
}

