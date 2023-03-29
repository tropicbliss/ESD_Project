use anyhow::Result;
use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use futures::TryStreamExt;
use graphql_client::{GraphQLQuery, Response};
use mongodb::{bson::doc, options::ClientOptions, Client, Collection};
use reqwest::Client as HttpClient;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::{net::SocketAddr, time::Duration};
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
    let shared_state = SharedState {
        db: collection,
        http: HttpClient::builder()
            .timeout(Duration::from_secs(9))
            .build()?,
    };
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

#[derive(GraphQLQuery)]
#[graphql(schema_path = "src/schema.json", query_path = "src/query.graphql")]
struct GetUser;

#[derive(Clone)]
struct SharedState {
    db: Collection<Comment>,
    http: HttpClient,
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

async fn does_groomer_exist(client: &HttpClient, id: &str) -> Result<bool, ApiError> {
    Ok(client
        .get(format!("http://groomer:5000/search/name/{id}"))
        .send()
        .await
        .map_err(|_| ApiError::InternalError)?
        .status()
        .is_success())
}

async fn does_user_exist(client: &HttpClient, name: &str) -> Result<bool, ApiError> {
    let variables = get_user::Variables {
        name: name.to_string(),
    };
    let request_body = GetUser::build_query(variables);
    let res = client
        .post(format!("http://user:5000/"))
        .json(&request_body)
        .send()
        .await
        .map_err(|_| ApiError::InternalError)?;
    let response_body: Response<get_user::ResponseData> =
        res.json().await.map_err(|_| ApiError::InternalError)?;
    Ok(response_body
        .data
        .ok_or(ApiError::InternalError)?
        .get_user
        .is_some())
}

async fn censor_comment(client: &HttpClient, comment: &str) -> Result<String, ApiError> {
    #[derive(Deserialize)]
    struct CensorerOutput {
        sanitised: String,
    }

    let json = json!({ "message": comment });
    let res: CensorerOutput = client
        .post("http://censorer:5000/")
        .json(&json)
        .send()
        .await
        .map_err(|_| ApiError::InternalError)?
        .json()
        .await
        .map_err(|_| ApiError::InternalError)?;
    Ok(res.sanitised)
}

async fn create_comment(
    state: State<SharedState>,
    Json(payload): Json<CreateInput>,
) -> Result<Json<CreateOutput>, ApiError> {
    payload.validate().map_err(|_| ApiError::InvalidData)?;
    let (user_exists, groomer_exists) = tokio::join!(
        does_user_exist(&state.http, &payload.user_name),
        does_groomer_exist(&state.http, &payload.groomer_name)
    );
    if !user_exists? {
        return Err(ApiError::UserDoesNotExist);
    }
    if !groomer_exists? {
        return Err(ApiError::GroomerDoesNotExist);
    }
    let (title, message) = tokio::join!(
        censor_comment(&state.http, &payload.title),
        censor_comment(&state.http, &payload.message)
    );
    let payload = Comment {
        groomer_name: payload.groomer_name,
        id: cuid::cuid2(),
        message: message?,
        rating: payload.rating,
        title: title?,
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
    let groomer_exist = does_groomer_exist(&state.http, &groomer_name).await?;
    if !groomer_exist {
        return Err(ApiError::GroomerDoesNotExist);
    }
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
    UserDoesNotExist,
    GroomerDoesNotExist,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let (status, error_message) = match self {
            ApiError::InternalError => (StatusCode::INTERNAL_SERVER_ERROR, "internal server error"),
            ApiError::InvalidData => (StatusCode::BAD_REQUEST, "invalid input data"),
            ApiError::UserDoesNotExist => (StatusCode::NOT_FOUND, "user cannot be found"),
            ApiError::GroomerDoesNotExist => (StatusCode::NOT_FOUND, "groomer cannot be found"),
        };
        let body = Json(json!({ "message": error_message }));
        (status, body).into_response()
    }
}
