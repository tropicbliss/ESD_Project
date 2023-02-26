use anyhow::Result;
use futures_lite::StreamExt;
use lapin::{
    options::{BasicAckOptions, BasicConsumeOptions, QueueDeclareOptions},
    types::FieldTable,
    Connection, ConnectionProperties,
};
use tracing::{debug, info};
use tracing_subscriber::{prelude::__tracing_subscriber_SubscriberExt, util::SubscriberInitExt};

fn main() -> Result<()> {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "logging=info".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    let addr = std::env::var("AMQP_ADDR")?;
    async_global_executor::block_on(async {
        let conn = Connection::connect(&addr, ConnectionProperties::default()).await?;
        info!("listening on {}", addr);
        let channel = conn.create_channel().await?;
        debug!(state=?conn.status().state());
        let queue = channel
            .queue_declare(
                "logs.*",
                QueueDeclareOptions::default(),
                FieldTable::default(),
            )
            .await?;
        debug!(?queue, "declared queue");
        debug!("will consume");
        let mut consumer = channel
            .basic_consume(
                "logs.*",
                "logger",
                BasicConsumeOptions::default(),
                FieldTable::default(),
            )
            .await?;
        debug!(state=?conn.status().state());
        while let Some(delivery) = consumer.next().await {
            debug!(message=?delivery, "received message");
            if let Ok(delivery) = delivery {
                async_global_executor::spawn(async move {
                    delivery.ack(BasicAckOptions::default()).await.unwrap();
                    let source = delivery.routing_key.as_str().split_once('.').unwrap().1;
                    let raw_message = delivery.data;
                    if let Ok(log_message) = String::from_utf8(raw_message) {
                        info!("{source} -> {log_message}");
                    }
                })
                .detach();
            }
        }
        Ok(())
    })
}
