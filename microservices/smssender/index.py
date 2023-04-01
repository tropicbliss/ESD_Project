import pika
from twilio.rest import Client
import os
import time

time.sleep(9)

ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
MESSAGING_SERVICE_SID = os.getenv("MESSAGING_SERVICE_SID")
client = Client(ACCOUNT_SID, AUTH_TOKEN)


def callback(channel, method, properties, body):
    recipient_type = method.routing_key.split('.')[1]
    contact_no = body.decode("utf-8")
    if recipient_type == "user":
        message = "Dear user, thanks for signing up with our service!"
    else:
        message = "Dear groomer, thanks for signing up with our service!"
    # client.messages.create(
    #     messaging_service_sid=MESSAGING_SERVICE_SID,
    #     body=message,
    #     to=contact_no
    # )


hostname = "esd-rabbit"
port = 5672

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=hostname, port=port,
                              heartbeat=3600, blocked_connection_timeout=3600)
)

channel = connection.channel()

exchange_name = "main"
exchange_type = "topic"
channel.exchange_declare(exchange=exchange_name,
                         exchange_type=exchange_type, durable=True)

queue_name = "sms"
channel.queue_declare(queue=queue_name, durable=True)

channel.queue_bind(exchange=exchange_name,
                   queue=queue_name, routing_key="sms.*")

channel.basic_consume(queue="sms", on_message_callback=callback, auto_ack=True)
channel.start_consuming()
