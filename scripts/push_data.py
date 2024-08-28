import boto3
import json
import base64
import sys
import datetime
import random
import uuid
import os
from uuid import UUID
import time
import threading

PROJECT_NAME = os.environ.get("PROJECT_NAME", "")
AWS_REGION = os.environ.get("AWS_REGION", "")
AWS_ACCOUNT = os.environ.get("AWS_ACCOUNT_ID", "")

OUTPUT_KEY = "StreamingService"
STACK_NAME = "StreamingServiceSingleStoreStack"

# Adjust the sleep time as needed for your streaming rate
STREAMING_RATE = 0.1
STREAMING_AMNT = 50

# Partition key for Kinesis
PARTITION_KEY = "vehicle_id"


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return obj.hex
        return json.JSONEncoder.default(self, obj)


def generate_sample_data():
    """Generates sample ingestion data"""
    vehicle_id = uuid.uuid4()
    timestamp = datetime.datetime.now().isoformat()
    location_lat = random.uniform(-90, 90)
    location_long = random.uniform(-180, 180)
    speed = random.uniform(0, 100)
    battery_level = random.uniform(0, 100)
    maintenance_status = random.choice(["OK", "NEEDS_MAINTENANCE"])
    passenger_count = random.randint(0, 4)
    return {
        "vehicle_id": vehicle_id,
        "ts": timestamp,
        "location_lat": location_lat,
        "location_long": location_long,
        "speed": speed,
        "battery_level": battery_level,
        "maintenance_status": maintenance_status,
        "passenger_count": passenger_count,
    }


def push_to_kinesis(stream_name, data):
    """Pushes data to Kinesis"""
    kinesis_client = boto3.client("kinesis", region_name=AWS_REGION)
    response = kinesis_client.put_record(
        StreamName=stream_name,
        Data=json.dumps(data, cls=UUIDEncoder).encode("utf-8"),
        PartitionKey=PARTITION_KEY,
    )
    return response


def push_to_sqs(queue_url, data):
    """Pushes data to SQS"""
    sqs_client = boto3.client("sqs", region_name=AWS_REGION)
    response = sqs_client.send_message(
        QueueUrl=queue_url, MessageBody=json.dumps(data, cls=UUIDEncoder)
    )
    return response


def get_provisioned_service():
    """Gets the provisioned service between SQS and Kinesis"""
    cf_client = boto3.client("cloudformation", region_name=AWS_REGION)
    try:
        response = cf_client.describe_stacks(StackName=STACK_NAME)
        stacks = response.get("Stacks", [])
        if not stacks:
            print(f"No stacks found with name {STACK_NAME}")
            sys.exit(1)
        stack = stacks[0]
        outputs = stack.get("Outputs", [])
        for output in outputs:
            if output["OutputKey"] == OUTPUT_KEY:
                return output["OutputValue"]
        print(f"Output key {OUTPUT_KEY} not found in stack {STACK_NAME}")
        sys.exit(1)
    except Exception as e:
        print(f"Error retrieving stack outputs: {e}")
        sys.exit(1)


def stream_data(service, target):
    try:
        for _ in range(STREAMING_AMNT):
            data = generate_sample_data()
            while True:
                if service == "Kinesis":
                    response = push_to_kinesis(target, data)
                elif service == "SQS":
                    response = push_to_sqs(target, data)
                print(f"Data pushed to {service}:", response)
                time.sleep(STREAMING_RATE)
    except KeyboardInterrupt:
        print("\nStreaming stopped.")


if __name__ == "__main__":
    service = get_provisioned_service()
    if service == "Kinesis":
        target = f"{PROJECT_NAME}-{AWS_ACCOUNT}-stream"
    elif service == "SQS":
        target = f"https://sqs.{AWS_REGION}.amazonaws.com/{AWS_ACCOUNT}/{PROJECT_NAME}-{AWS_ACCOUNT}-queue"
    stream_data(service, target)
