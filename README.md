#spider search engine

Public IP address of live web server: 54.172.36.115
# spider search engine
Public DNS of web server: http://ec2-54-172-36-115.compute-1.amazonaws.com

Deployment and termination script instructions:

Deployment script location: spider_search_engine/app/deploy_search_engine.sh
Usage: ./deploy_search_engine.sh
Pre-setup: User MUST specify a AWS credential file in ~/.boto , where .boto is the file name. The file name and location MUST be exact!
The file MUST have a format of:

[Credentials]
aws_access_key_id = <YOUR_AWS_ACCESS_KEY_ID>
aws_secret_access_key = <YOUR_AWS_SECRET_ACCESS_KEY>

NOTE: AWS access key and secret DOES NOT NEED quotes in between. 
xUHEEUWk ==> acceptable
"xUHEEUWk" ==> NOT acceptable

Termination script location: spider_search_engine/app/stop_search_engine.py
Usage: python stop_search_engine.py <instance_id_to_terminate>
Pre-setup: Same as deployment script instruction.

Code organization:

spider_search_engine has 3 directories:
- front_end: front end component code and data access object to Dynamo DB
- back_end: back end component code
- app: Scripts needed to deploy and stop search engine on EC2 instance