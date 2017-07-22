#ifndef RULE_H
#define RULE_H

#include <iostream>
#include <string>
#include <boost/dynamic_bitset.hpp>

class Rule{
public:
	Rule();
	Rule(int id, int switch_id, std::string prefix, std::string in_header, int in_port, int out_port, int priority, int path_index);
	~Rule();
	
	boost::dynamic_bitset<> headerspaceTransform(std::string header);

	int getID();
	int getSwitchID();
	std::string getInHeader();
	boost::dynamic_bitset<> getInHeaderSpace();
	boost::dynamic_bitset<> getOutHeaderSpace();
	int getInPort();
	int getOutPort();
	int getPriority();
	std::string getPrefix();

	void setField(std::string field);

	void print();

private:
	int id;
	int switch_id;
	std::string prefix;
	std::string in_header;
	int in_port;
	int out_port;
	int priority;
	int path_index;

	boost::dynamic_bitset<> in_headerspace{64};
	boost::dynamic_bitset<> out_headerspace{64};

	//not use
	std::string set_field;
	boost::dynamic_bitset<> set_field_headerspace{64};
	boost::dynamic_bitset<> set_field_headerspace2{64};
};

#endif


