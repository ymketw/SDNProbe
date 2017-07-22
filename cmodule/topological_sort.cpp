#include "topological_sort.hpp"

TopologicalSort::TopologicalSort(int vertex_number, std::unordered_map<int, Vertex> *ori_rule_graph, std::unordered_map<int, int> *rule_grpah_index_id){
	this->sorting_list.reserve(vertex_number);
	this->indegree.reserve(vertex_number);
	this->vertex_number = vertex_number;
	for ( int i = 0; i < vertex_number; i++ ){
		int rule_id = rule_grpah_index_id->at(i);
		this->rule_grpah[rule_id] = Vertex(ori_rule_graph->at(rule_id));
		this->indegree[rule_id] = ori_rule_graph->at(rule_id).getInNeighbors()->size();

		this->rule_grpah[rule_id].getOutNeighbors()->clear();
	}
}

TopologicalSort::~TopologicalSort(){
}

void TopologicalSort::start(std::unordered_map<int, Vertex> *ori_rule_graph, std::unordered_map<int, int> *rule_grpah_index_id){
	std::queue<int> vertex_queue;
	for ( int i = 0; i < this->vertex_number; i++ ){
		int rule_id = rule_grpah_index_id->at(i);
		if ( this->indegree.at(rule_id) == 0 ){
			vertex_queue.push(rule_id);
		}
	}
	while ( !vertex_queue.empty() ){
		int u = vertex_queue.front();
		vertex_queue.pop();
		this->sorting_list.push_back(u);
		for ( unsigned int i = 0; i < ori_rule_graph->at(u).getInNeighbors()->size(); i++ ){
			int v = ori_rule_graph->at(u).getInNeighbors()->at(i);
			this->rule_grpah.at(v).addOutNeighbor(u);
		}
		for ( unsigned int i = 0; i < ori_rule_graph->at(u).getOutNeighbors()->size(); i++ ){
			int v = ori_rule_graph->at(u).getOutNeighbors()->at(i);
			this->indegree.at(v)--;
			if ( this->indegree.at(v) == 0 ){
				vertex_queue.push(v);
			}
		}
	}
}

std::vector<int>* TopologicalSort::getSortingList(){
	return &this->sorting_list;
}

std::unordered_map<int, Vertex>* TopologicalSort::getRuleGraph(){
	return &this->rule_grpah;
}

void TopologicalSort::printSortingList(){
	std::cout << "Topological sorting: " << std::endl;
	for ( unsigned int i = 0; i < this->sorting_list.size(); i++ ){
		std::cout << sorting_list[i] << " ";
	}
	std::cout << std::endl;
}
