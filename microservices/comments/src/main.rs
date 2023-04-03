use anyhow::Result;
use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use futures::TryStreamExt;
use mongodb::{bson::doc, options::ClientOptions, Client, Collection};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::net::SocketAddr;
use tracing_subscriber::{prelude::__tracing_subscriber_SubscriberExt, util::SubscriberInitExt};
use validator::Validate;

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "comments=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();
    let client_options = ClientOptions::parse(&std::env::var("DB_URI")?).await?;
    let client = Client::with_options(client_options)?;
    let database =
        client.database(&std::env::var("DATABASE").unwrap_or_else(|_| "esdproject".into()));
    let collection = database
        .collection::<Comment>(&std::env::var("COLLECTION").unwrap_or_else(|_| "comments".into()));
    let shared_state = SharedState { db: collection };
    let app = Router::new()
        .route("/", post(create_comment))
        .route("/:id", get(get_comment))
        .with_state(shared_state);
    let addr = std::env::var("ADDR").unwrap_or_else(|_| "127.0.0.1:3000".into());
    let addr: SocketAddr = addr.parse()?;
    tracing::debug!("listening on {addr}");
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await?;
    Ok(())
}

#[derive(Clone)]
struct SharedState {
    db: Collection<Comment>,
}

#[derive(Serialize, Deserialize)]
struct Comment {
    id: String,
    user_name: String,
    groomer_name: String,
    title: String,
    message: String,
    rating: u8,
}

#[derive(Deserialize, Validate)]
#[serde(rename_all = "camelCase")]
struct CreateInput {
    user_name: String,
    groomer_name: String,
    title: String,
    message: String,
    #[validate(range(min = 1, max = 5))]
    rating: u8,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct CreateOutput {
    id: String,
    title: String,
    message: String,
}

async fn create_comment(
    state: State<SharedState>,
    Json(payload): Json<CreateInput>,
) -> Result<Json<CreateOutput>, ApiError> {
    payload.validate().map_err(|_| ApiError::InvalidData)?;
    let payload = Comment {
        groomer_name: payload.groomer_name,
        id: cuid::cuid2(),
        message: payload.message,
        rating: payload.rating,
        title: payload.title,
        user_name: payload.user_name,
    };
    state
        .db
        .insert_one(&payload, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    Ok(Json(CreateOutput {
        id: payload.id,
        title: payload.title,
        message: payload.message,
    }))
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct GetOutput {
    id: String,
    user_name: String,
    title: String,
    message: String,
    rating: u8,
}

async fn get_comment(
    Path(groomer_name): Path<String>,
    state: State<SharedState>,
) -> Result<Json<Vec<GetOutput>>, ApiError> {
    let filter = doc! {"groomer_name": groomer_name};
    let res = state
        .db
        .find(filter, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res = res
        .into_iter()
        .map(|c| GetOutput {
            id: c.id,
            message: c.message,
            rating: c.rating,
            title: c.title,
            user_name: c.user_name,
        })
        .collect();
    Ok(Json(res))
}

#[derive(Debug)]
enum ApiError {
    InternalError,
    InvalidData,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let (status, error_message) = match self {
            ApiError::InternalError => (StatusCode::INTERNAL_SERVER_ERROR, "internal server error"),
            ApiError::InvalidData => (StatusCode::BAD_REQUEST, "invalid input data"),
        };
        let body = Json(json!({ "message": error_message }));
        (status, body).into_response()
    }
}
