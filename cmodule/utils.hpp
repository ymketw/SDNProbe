#ifndef UTILS_H
#define UTILS_H

#include <boost/dynamic_bitset.hpp>

bool is_match(boost::dynamic_bitset<> r1, boost::dynamic_bitset<> r2);
boost::dynamic_bitset<> intersection(boost::dynamic_bitset<> r1, boost::dynamic_bitset<> r2);
bool is_zero(boost::dynamic_bitset<> r1);

#endif
