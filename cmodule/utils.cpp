#include "utils.hpp"

bool is_match(boost::dynamic_bitset<> r1, boost::dynamic_bitset<> r2){
	boost::dynamic_bitset<> match = (r1 & r2);
	boost::dynamic_bitset<> mask{r1.size()};
	boost::dynamic_bitset<> zero{r1.size()};
	mask[0] = 1;
	mask[1] = 1;
	while ( mask != zero ){
		if ( (match & mask) == zero ){
			return false;
		}
		mask = mask << 2;
	}
	return true;
}
 
boost::dynamic_bitset<> intersection(boost::dynamic_bitset<> r1, boost::dynamic_bitset<> r2){
	boost::dynamic_bitset<> zero{r1.size()};
	boost::dynamic_bitset<> in{r1.size()};
	if ( !is_match(r1, r2) ) return zero;
	return (r1 & r2);
}

bool is_zero(boost::dynamic_bitset<> r1){
	boost::dynamic_bitset<> zero{r1.size()};
	if ( r1 == zero ) return true;
	return false;
}
