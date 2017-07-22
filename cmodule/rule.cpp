#include <iostream>

#include "rule.hpp"

Rule::Rule(){
}

Rule::Rule(int id, int switch_id, std::string prefix, std::string in_header, int in_port, int out_port, int priority, int path_index){
	this->id = id;
	this->switch_id = switch_id;
	this->prefix = prefix;
	this->in_header = in_header;
	this->in_port = in_port;
	this->out_port = out_port;
	this->priority = priority;
	this->path_index = path_index;

	this->in_headerspace = this->headerspaceTransform(in_header);
	this->out_headerspace = this->headerspaceTransform(in_header);
}

Rule::~Rule(){
}

boost::dynamic_bitset<> Rule::headerspaceTransform(std::string header){
	boost::dynamic_bitset<> hs{64};
	for ( int i = header.length()-1, j = 0; i >= 0; i--, j += 2 ){
		if ( header[i] == 'x' ){
			hs[j] = 1;
			hs[j+1] = 1;
		}
		else if ( header[i] == '0' ){
			hs[j] = 1;
			hs[j+1] = 0;
		}
		else if ( header[i] == '1' ){
			hs[j] = 0;
			hs[j+1] = 1;
		}
		else if ( header[i] == 'z' ){
			hs[j] = 0;
			hs[j+1] = 0;
		}
		else{
			std::cerr << "Wrong headerspace" << std::endl;
		}
	}
	return hs;
}

int Rule::getID(){
	return this->id;
}

int Rule::getSwitchID(){
	return this->switch_id;
}

std::string Rule::getInHeader(){
	return this->in_header;
}

boost::dynamic_bitset<> Rule::getInHeaderSpace(){
	return this->in_headerspace;
}

boost::dynamic_bitset<> Rule::getOutHeaderSpace(){
	return this->in_headerspace;
}

int Rule::getInPort(){
	return this->in_port;
}

int Rule::getOutPort(){
	return this->out_port;
}

int Rule::getPriority(){
	return this->priority;
}

std::string Rule::getPrefix(){
	return this->prefix;
}

void Rule::setField(std::string field){
	this->set_field = field;
	this->set_field_headerspace = this->headerspaceTransform(field);

	std::string field2 = field;
	for ( int i = 0; (unsigned int)i < field.length(); i++ ){
		if ( field[i] == 'x' ){
			field2.replace(i, 1, std::string("z"));
		}		
	}
	this->set_field_headerspace2 = this->headerspaceTransform(field2);

}

void Rule::print(){
	std::cout << "ID: " << this->id << " ";
	std::cout << "Switch ID: " << this->switch_id << " ";
	std::cout << "Prefix: " << this->prefix << " ";
	std::cout << "Headerspace: " << this->in_headerspace << " ";
	std::cout << "Inport: " << this->in_port << " ";
	std::cout << "Outport: " << this->out_port << " ";
	std::cout << "Priority: " << this->priority << " ";
	std::cout << "Path index: " << this->path_index << " ";
	std::cout << std::endl;
}
