from boto.ec2 import connect_to_region
import time
import sys

""" Launch an EC2 instance and write its dns name and instance id into properties file and finishes after the instance is stable. """

KEY_PAIR = "spider"
SECURITY_GROUP = "spider"
DIR = "/tmp"

# Launch EC2 instance.
print "Deploying EC2 instance for search engine..."
conn = connect_to_region("us-east-1")
keyPair = conn.create_key_pair(KEY_PAIR)
saved = keyPair.save(DIR)
securityGroup = conn.create_security_group(SECURITY_GROUP, "spider search engine")
securityGroup.authorize("icmp", -1, -1, "0.0.0.0/0")
securityGroup.authorize("tcp", 22, 22, "0.0.0.0/0")
securityGroup.authorize("tcp", 80, 80, "0.0.0.0/0")
reservation = conn.run_instances("ami-9eaa1cf6", key_name=KEY_PAIR, security_groups=[SECURITY_GROUP], instance_type="t2.micro")
instance = reservation.instances[0]
instance_id = instance.id

# Poll until EC2 instance status changes from pending to running
print "Instance is pending... please wait patiently"
while instance.state != "running":
    time.sleep(2)
    instance.update()

# Write dns name and instance id into properties file, so that later on bash script could pick up those values.
file = open(DIR + "/search-engine-info.properties", "w+")
file.write("dns_name="+ instance.dns_name + "\n")
file.write("instance_id=" + instance.id + "\n")
file.write("key_pair_abs_path=" + DIR + "/" + KEY_PAIR + ".pem")
file.close()

# Instance needs some time to initialize its system so that we could ssh to it. So give some time buffer before we ssh to the instance.
print "Instance is running and is initializing its system. We would be able to ssh to the instance to deploy our search engine once initiization is done. This might take a few minutes."

is_system_ready = False
while is_system_ready == False:
    instances = conn.get_all_instance_status()
    for instance in instances:
        system_status = instance.system_status.status
        instance_status = instance.instance_status.status

        if instance_id == instance.id:
            if system_status == 'ok' and instance_status == 'ok':
                is_system_ready = True
                break
            else:
                time.sleep(2)
                print '.',
                sys.stdout.flush()

print "\nInstance is ready! ssh to the instance now to deploy our search engine!"
