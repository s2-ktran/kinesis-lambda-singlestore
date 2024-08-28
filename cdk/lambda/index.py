import boto3
import json
import base64
import os
import pymysql
import datetime

# Database configuration
SERVICE = os.environ.get("SERVICE", "")
SECRET_NAME = os.environ.get("SECRET_NAME", "")
REGION_NAME = os.environ.get("REGION", "")


def connect_singlestore(host, user, password, db):
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        db=db,
        cursorclass=pymysql.cursors.DictCursor,
    )


def process_payload(table, payload):
    columns = ", ".join(payload.keys())
    values = ", ".join(f"'{v}'" for v in payload.values())
    sql_statement = f"INSERT INTO {table} ({columns}) VALUES ({values});\n"
    return sql_statement


def handler(event, context):
    print(event)
    timestamp = datetime.datetime.now().isoformat(timespec="milliseconds")
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=REGION_NAME)
    sql_statement = ""
    unique_entry = []
    try:
        # Fetch the secret value
        response = client.get_secret_value(SecretId=SECRET_NAME)

        # Parse the secret value
        secret = json.loads(response["SecretString"])
        user = secret["DB_USERNAME"]
        password = secret["PASSWORD"]
        host = secret["ENDPOINT"]
        db = secret["DATABASE_NAME"]
        table = secret["DESTINATION_TABLE"]

        for record in event["Records"]:
            if SERVICE == "Kinesis":
                payload = base64.b64decode(record["kinesis"]["data"]).decode("utf-8")
                print(payload)
                payload = json.loads(payload)
                payload["kinesis_ts"] = datetime.datetime.fromtimestamp(
                    record["kinesis"]["approximateArrivalTimestamp"]
                ).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )  #
                payload["lambda_ts"] = timestamp
            elif SERVICE == "SQS":
                payload = json.loads(record["body"])
            if payload["vehicle_id"] not in unique_entry:
                unique_entry.append(payload["vehicle_id"])
                sql_statement += process_payload(table, payload)
            print("SQL Statements", sql_statement)
        connection = connect_singlestore(host, user, password, db)
        with connection.cursor() as cursor:
            cursor.execute(sql_statement)
            connection.commit()
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        connection.close()
        print("Connection closed")

    return {
        "statusCode": 200,
        "body": json.dumps("SQL statements written to S2 successfully"),
    }


if __name__ == "__main__":
    example_data = {
        "Records": [
            {
                "messageId": "f4828336-75e3-4f64-b89c-ad3157d30135",
                "receiptHandle": "AQEBI+E6+tD4weCuqLaEHiTs3Hagtkcp4l4RaIoFvY++HfkwfnmrRkJSWmLol+ZrxRj42/I9l5GRm90CItYzdQzSpXWZ1BGlyOjK+qwuEkRRZwwL9ENkLC8Uxs4BxTHoCiQifAxXthvavBtgJwpJ+Xeb3MWeaJ6L5Xl+xeDv+S/HOxRuaTHDbMfnjseor6CGbhaNUYrz6T/eQxZ3Lr+qBVhMANWG6vQYqtU1VeoEwz2p7xEdGI+mXGKbQljCmV1z/rgzzgRBLMmLMhtjjpjVBJ1AnlqHXBwyybe7hWLOinbnAkCbV0iw05YlIyA7bLwqtsxbamf/aEpHP/i651/rU1FuNGzpgI74ZnaSofR3tAgpSHTia5SL7NNqcKd9x7NLt7J/689OV+saI001LPcVJq28jA==",
                "body": '{"vehicle_id": "781b16dedc694018a5a77893b4cb40ce", "timestamp": "2024-07-24T10:30:58.292702", "location_lat": 73.00168204649029, "location_long": -149.8795304348423, "speed": 52.95178012882374, "battery_level": 5.705126837792685, "maintenance_status": "OK", "passenger_count": 4}',
                "attributes": {
                    "ApproximateReceiveCount": "7",
                    "SentTimestamp": "1721842259518",
                    "SenderId": "AIDA6GBMH5LITKYTK5CJD",
                    "ApproximateFirstReceiveTimestamp": "1721842259525",
                },
            },
        ]
    }
    handler(example_data, {})
