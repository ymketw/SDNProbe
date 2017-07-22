#include "transitive_closure.hpp"

TransitiveClosure::TransitiveClosure(int vertex_number, std::unordered_map<int, Vertex> *ori_rule_graph, std::unordered_map<int, int> *rule_graph_index_id){
	this->vertex_number = vertex_number;

	for ( int i = 0; i < vertex_number; i++ ){
		int rule_id = rule_graph_index_id->at(i);
		this->rule_graph[rule_id] = Vertex(ori_rule_graph->at(rule_id));
		this->rule_graph[rule_id].getOutNeighbors()->clear();
		this->rules[rule_id] = ori_rule_graph->at(rule_id).getRule()->getInHeaderSpace();
		this->P[rule_id][rule_id] = -1;
	}
}

TransitiveClosure::~TransitiveClosure(){
}

void TransitiveClosure::start(std::unordered_map<int, Vertex> *ori_rule_graph, std::unordered_map<int, int> *rule_graph_index_id){
	for ( int i = 0; i < this->vertex_number; i++  ){
		int u = rule_graph_index_id->at(i);
		this->BFS(ori_rule_graph, u);
	}
}

void TransitiveClosure::BFS(std::unordered_map<int, Vertex> *ori_rule_graph, int u){
	std::queue<int> vertex_queue;
	std::unordered_map<int, int> visited;
	this->rules[u] = ori_rule_graph->at(u).getRule()->getInHeaderSpace();
	vertex_queue.push(u);
	visited[u] = 1;

	while ( !vertex_queue.empty() ){
		int v = vertex_queue.front();
		vertex_queue.pop();
		for ( unsigned int i = 0; i < ori_rule_graph->at(v).getOutNeighbors()->size(); i++ ){
			int w = ori_rule_graph->at(v).getOutNeighbors()->at(i);
			if ( visited[w] == 1 ){
				continue;
			}
			rules[w] = intersection(rules[v], rules[w]);
			if ( !is_zero(rules[w]) ){
				this->rule_graph[u].addOutNeighbor(w);
				vertex_queue.push(w);
				visited[w] = 1;
				this->P[u][w] = v;
				//std::cerr << u << " " << w <<  " " << P[u][w] << std::endl;
			}
		}
	}
}

std::unordered_map<int, Vertex>* TransitiveClosure::getRuleGraph(){
	return &this->rule_graph;
}


std::unordered_map<int, std::unordered_map<int, int> >* TransitiveClosure::getP(){
	return &this->P;
}

