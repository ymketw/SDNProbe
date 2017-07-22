#include "trace_path.hpp"

TracePath::TracePath(int vertex_number, std::unordered_map<int, int> *rule_graph_index_id){
	this->vertex_number = vertex_number;
	for ( int i = 0; i < vertex_number; i++ ){
		this->all_paths.reserve(vertex_number/10);
		int rule_id = rule_graph_index_id->at(i);
		visited[rule_id] = 0;
	}

}

TracePath::~TracePath(){}

void TracePath::start(std::unordered_map<int, int> *match, std::unordered_map<int, std::unordered_map<int, int> > *P, std::vector<int> *sorting_vertices){
	for ( unsigned int i = 0; i < sorting_vertices->size(); i++ ){
		int u = sorting_vertices->at(i);
		if ( this->visited[u] == 1 ) continue;
		this->visited[u] = 1;

		std::vector<int> path;
		path.reserve(8);
		path.push_back(u);
		int v = match->at(u);
		while ( v != -1 ){
			this->visited[v] = 1;
			std::vector<int> sub_path;
			int w = v;
			while( P->at(u).at(w) != -1 ){
				sub_path.push_back(w);
				w = P->at(u).at(w);
			}
			std::reverse(sub_path.begin(), sub_path.end());
			path.reserve(path.size()+sub_path.size());
			path.insert(path.end(), sub_path.begin(), sub_path.end());
			u = v;
			v = match->at(u);
		}
		this->all_paths.push_back(path);
	}
}

void TracePath::print(){
	for ( unsigned int i = 0; i < this->all_paths.size(); i++  ){
		for ( auto id : this->all_paths.at(i) ){
			std::cout << id << " ";
		}
		std::cout << std::endl;
	}
}

std::vector<std::vector<int> >* TracePath::getAllPaths(){
	return &this->all_paths;
}
