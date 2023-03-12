import pika
import os
import json
from twilio.rest import Client

account_sid = os.environ("ACCOUNT_SID")
auth_token = os.environ("AUTH_TOKEN")
client = Client(account_sid, auth_token)
phone_no = os.environ("PHONE_NO")

hostname = os.environ("HOSTNAME")
port = os.environ("PORT")

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=hostname, port=port,
                              heartbeat=3600, blocked_connection_timeout=3600)
)
channel = connection.channel()
exchange_name = "order_topic"
exchange_type = "topic"
channel.exchange_declare(exchange=exchange_name,
                         exchange_type=exchange_type, durable=True)

queue_name = "Email"
channel.queue_declare(queue=queue_name, durable=True)
channel.queue_bind(exchange=exchange_name,
                   queue=queue_name, routing_key="email")


def on_receive(channel, method, properties, body):
    j = json.loads(body)
    phone = j["phone"]
    client.messages.create(messaging_service_sid=phone_no,
                           body="Successfully created an account!", to=phone)


channel.basic_consume(
    queue=queue_name, on_message_callback=on_receive, auto_ack=True)
