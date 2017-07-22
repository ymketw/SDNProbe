#include "test_packet.hpp"

TestPacket::TestPacket(int index, std::vector<int> original_path, std::unordered_map<int, Rule> *rules){
	this->index = index;
	this->is_discard = false;
	//std::copy(original_path.begin(), original_path.end(), this->path.begin());
	path = original_path;
	this->prefix = rules->at(path[0]).getPrefix();
	this->header_space = rules->at(path[0]).getInHeaderSpace();
	for ( unsigned int i = 0; i < this->path.size(); i++ ){
		int rule_id = path.at(i);
		this->header_space = intersection(header_space, rules->at(rule_id).getInHeaderSpace());
	}
}

TestPacket::~TestPacket(){
}

int TestPacket::getIndex(){
	return this->index;
}

std::vector<int>* TestPacket::getPath(){
	return &this->path;
}

std::string TestPacket::getPrefix(){
	return this->prefix;
}

void TestPacket::setDiscard(){
	this->is_discard =true;
}

bool TestPacket::isDiscard(){
	return this->is_discard;
}

void TestPacket::print(){
	std::cout << this->index << " " << this->header_space << " ";
   	std::cout << this->prefix << " ";
	for ( auto &i : this->path ){
		std::cout << i << " ";
	}
	std::cout << std::endl;
}
