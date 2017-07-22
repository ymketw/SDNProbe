#ifndef TEST_PACKET_H
#define TEST_PACKET_H

#include <vector>
#include <unordered_map>
#include <algorithm>
#include <boost/dynamic_bitset.hpp>

#include "rule.hpp"
#include "utils.hpp"

class TestPacket{
public:
	TestPacket(int index, std::vector<int> original_path, std::unordered_map<int, Rule> *rules);
	~TestPacket();

	int getIndex();
	std::vector<int>* getPath();
	std::string getPrefix();

	void setDiscard();
	bool isDiscard();
	void print();

private:
	int index;
	bool is_discard;
	std::vector<int> path;
	std::string prefix;
	boost::dynamic_bitset<> header_space;
};

#endif
