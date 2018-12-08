#!/bin/sh
# Main entry point of deploying search engine!

# Install boto so that start_aws.py understands import of boto
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py --user
~/.local/bin/pip install boto --user

# Launch EC2 instance and populate dns name and instance id into a properties file.
python start_aws.py

# Load properties file that has dns name, key pair path and instance id
. /tmp/search-engine-info.properties

# scp AWS credential file passed in by user to EC2 instance
scp -o StrictHostKeyChecking=no -i "${key_pair_abs_path}" ~/.boto ubuntu@"${dns_name}":~/.boto

# scp properties file that has public dns name to EC2 instance
scp -o StrictHostKeyChecking=no -i "${key_pair_abs_path}" /tmp/search-engine-info.properties ubuntu@"${dns_name}":/tmp/

# SSH to EC2 instance and run deploy_search_engine_helper.sh on EC2 instance. It installs package required to run the search engine.
# Then it runs the search engine in background.
ssh -o StrictHostKeyChecking=no -i "${key_pair_abs_path}" ubuntu@"${dns_name}" < deploy_search_engine_helper.sh

# Print dns name and instance id back to user.
echo "Deployment of search engine is successful!"
echo "Public DNS of the server is ${dns_name}"
echo "Instance id of the server is ${instance_id}"