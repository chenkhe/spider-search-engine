import sys
from boto.ec2 import connect_to_region

def stop(instance_id):
    conn = connect_to_region("us-east-1")
    try:
        res = conn.terminate_instances([instance_id])
    except Exception as e:
        return "Failed to terminate instance with id " + str(instance_id) + ".\nException message: " + str(e)

    if res[0].id == instance_id:
        return "Terminated instance with id " + instance_id + " successfully!"

print stop(sys.argv[1])