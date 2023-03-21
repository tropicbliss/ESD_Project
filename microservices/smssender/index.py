import pika
from twilio.rest import Client
import os

ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
MESSAGING_SERVICE_SID = os.getenv("MESSAGING_SERVICE_SID")
client = Client(ACCOUNT_SID, AUTH_TOKEN)


def callback(channel, method, properties, body):
    recipient_type = method.routing_key[1]
    contact_no = body.decode("utf-8")
    if recipient_type == "user":
        message = "Dear user, thanks for signing up with our service!"
    else:
        message = "Dear groomer, thanks for signing up with our service!"
    client.messages.create(
        messaging_service_sid=MESSAGING_SERVICE_SID,
        body=message,
        to=contact_no
    )


hostname = "esd-rabbit"
port = 5672

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=hostname, port=port,
                              heartbeat=3600, blocked_connection_timeout=3600)
)

channel = connection.channel()

channel.basic_consume(queue="sms", on_message_callback=callback, auto_ack=True)
channel.start_consuming()
