#!/bin/sh
sudo apt-get install git -y
sudo apt-get update
sudo rm -Rf spider_search_engine/
git clone https://chenkhe:998001@bitbucket.org/sandw723/spider_search_engine.git
sudo apt-get install python-pip -y
sudo apt-get update
sudo pip install bottle
sudo pip install --upgrade google-api-python-client
sudo pip install beaker
sudo pip install -U boto
sudo apt-get install python-gevent -y
sudo apt-get update
# Load properties file that has public dns name
. /tmp/search-engine-info.properties
cd /home/ubuntu/spider_search_engine/front_end
nohup sudo python server.py http://"${dns_name}" > search_engine.out 2> search_engine.err < /dev/null &