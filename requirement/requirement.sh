#!/bin/bash

#Install Ryu
sudo pip install ryu

#Install NumPy
sudo apt-get -y install python-numpy

#Install graph-tool
sudo apt-key adv --keyserver pgp.skewed.de --recv-key 98507F25
echo 'deb http://downloads.skewed.de/apt/trusty trusty universe' | sudo tee -a  /etc/apt/sources.list
echo 'deb-src http://downloads.skewed.de/apt/trusty trusty universe' | sudo tee -a  /etc/apt/sources.list
sudo apt-get update
sudo apt-get -y --force-yes install python-graph-tool

#Install blessings
sudo pip install blessings

#Install boost
sudo apt-get install libboost-all-dev

#Install OpenMP
sudo apt-get -y install gcc-multilib

#Install Mininet
sudo apt-get install mininet
