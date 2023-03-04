use anyhow::Result;
use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use futures::{stream, StreamExt, TryStreamExt};
use graphql_client::{GraphQLQuery, Response};
use mongodb::{
    bson::{doc, DateTime},
    options::ClientOptions,
    Client, Collection,
};
use reqwest::Client as HttpClient;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::{
    collections::{HashMap, HashSet},
    net::SocketAddr,
    time::Duration,
};
use tracing_subscriber::{prelude::__tracing_subscriber_SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "appointments=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();
    let client_options = ClientOptions::parse(&std::env::var("DB_URI")?).await?;
    let client = Client::with_options(client_options)?;
    let database =
        client.database(&std::env::var("DATABASE").unwrap_or_else(|_| "appointments".into()));
    let collection = database.collection::<Appointment>(
        &std::env::var("COLLECTION").unwrap_or_else(|_| "appointments".into()),
    );
    let shared_state = SharedState {
        db: collection,
        http: HttpClient::builder()
            .timeout(Duration::from_secs(3))
            .build()?,
    };
    let app = Router::new()
        .route("/user/:id", get(get_user))
        .route("/signin/:id", get(get_arriving_customers))
        .route("/staying/:id", get(get_staying_customers))
        .route("/status/:id", post(change_appointment_status))
        .route("/create", post(create_appointment))
        .route("/stayed", post(stayed_customers))
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

async fn does_groomer_exist(client: &HttpClient, id: &str) -> Result<bool, ApiError> {
    Ok(client
        .get(format!("http://groomer:5000/read/{id}"))
        .send()
        .await
        .map_err(|_| ApiError::InternalError)?
        .status()
        .as_u16()
        == 200)
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

#[derive(Clone)]
struct SharedState {
    db: Collection<Appointment>,
    http: HttpClient,
}

#[derive(Serialize, Deserialize)]
struct Appointment {
    id: String,
    user_name: String,
    groomer_id: String,
    start_date: DateTime,
    end_date: DateTime,
    status: String,
    pets: Vec<Pet>,
}

#[derive(Deserialize, Serialize)]
struct Pet {
    pet_type: String,
    name: String,
    gender: String,
    age: usize,
    medical_info: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct UserEndpointOutput {
    groomer_id: String,
    groomer_name: String,
    start_date: String,
    end_date: String,
    groomer_picture_url: String,
    pet_names: Vec<String>,
}

async fn get_user(
    Path(user_name): Path<String>,
    state: State<SharedState>,
) -> Result<Json<Vec<UserEndpointOutput>>, ApiError> {
    #[derive(Deserialize)]
    struct UserReadEndpointOutput {
        name: String,
        picture_url: String,
    }

    if !does_user_exist(&state.http, &user_name).await? {
        return Err(ApiError::UserDoesNotExist);
    }
    let filter = doc! {"user_name": user_name};
    let res = state
        .db
        .find(filter, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::InternalError)?;
    let groomers: HashSet<String> = res.iter().map(|app| app.groomer_id.clone()).collect();
    let groomer_info: HashMap<String, UserReadEndpointOutput> = stream::iter(groomers)
        .map(|id| {
            let client = &state.http;
            async move {
                let json = json!({ "id": id });
                let res: UserReadEndpointOutput = client
                    .post("http://groomer:5000/read")
                    .json(&json)
                    .send()
                    .await
                    .unwrap()
                    .json()
                    .await
                    .unwrap();
                (id, res)
            }
        })
        .buffer_unordered(3)
        .collect()
        .await;
    let res = res
        .into_iter()
        .map(|app| UserEndpointOutput {
            end_date: app.end_date.try_to_rfc3339_string().unwrap(),
            groomer_name: groomer_info.get(&app.groomer_id).unwrap().name.clone(),
            groomer_picture_url: groomer_info
                .get(&app.groomer_id)
                .unwrap()
                .picture_url
                .clone(),
            groomer_id: app.groomer_id,
            pet_names: app.pets.into_iter().map(|pet| pet.name).collect(),
            start_date: app.start_date.try_to_rfc3339_string().unwrap(),
        })
        .collect();
    Ok(Json(res))
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct SignInOutput {
    id: String,
    user_name: String,
    start_date: String,
    end_date: String,
    pets: Vec<Pet>,
}

async fn get_arriving_customers(
    Path(groomer_id): Path<String>,
    state: State<SharedState>,
) -> Result<Json<Vec<SignInOutput>>, ApiError> {
    #[derive(Deserialize)]
    struct UserReadEndpointOutput {
        name: String,
    }

    if !does_groomer_exist(&state.http, &groomer_id).await? {
        return Err(ApiError::GroomerDoesNotExist);
    }
    let filter = doc! {"groomer_id": groomer_id, "status": "awaiting"};
    let res = state
        .db
        .find(filter, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res = stream::iter(res)
        .map(|app| {
            let client = &state.http;
            async move {
                let res: UserReadEndpointOutput = client
                    .get(format!("http://user:5000/read/{}", app.user_name))
                    .send()
                    .await
                    .unwrap()
                    .json()
                    .await
                    .unwrap();
                SignInOutput {
                    end_date: app.end_date.try_to_rfc3339_string().unwrap(),
                    id: app.id,
                    pets: app.pets,
                    start_date: app.start_date.try_to_rfc3339_string().unwrap(),
                    user_name: res.name,
                }
            }
        })
        .buffer_unordered(3)
        .collect()
        .await;
    Ok(Json(res))
}

async fn get_staying_customers(
    Path(groomer_id): Path<String>,
    state: State<SharedState>,
) -> Result<Json<Vec<SignInOutput>>, ApiError> {
    #[derive(Deserialize)]
    struct UserReadEndpointOutput {
        name: String,
    }

    if !does_groomer_exist(&state.http, &groomer_id).await? {
        return Err(ApiError::GroomerDoesNotExist);
    }
    let filter = doc! {"groomer_id": groomer_id, "status": "staying"};
    let res = state
        .db
        .find(filter, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res = stream::iter(res)
        .map(|app| {
            let client = &state.http;
            async move {
                let res: UserReadEndpointOutput = client
                    .get(format!("http://user:5000/read/{}", app.user_name))
                    .send()
                    .await
                    .unwrap()
                    .json()
                    .await
                    .unwrap();
                SignInOutput {
                    end_date: app.end_date.try_to_rfc3339_string().unwrap(),
                    id: app.id,
                    pets: app.pets,
                    start_date: app.start_date.try_to_rfc3339_string().unwrap(),
                    user_name: res.name,
                }
            }
        })
        .buffer_unordered(3)
        .collect()
        .await;
    Ok(Json(res))
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct StatusChangeInput {
    status: String,
}

const STATUSES: [&'static str; 3] = ["awaiting", "staying", "left"];

async fn change_appointment_status(
    Path(appointment_id): Path<String>,
    state: State<SharedState>,
    Json(payload): Json<StatusChangeInput>,
) -> Result<StatusCode, ApiError> {
    if !STATUSES.contains(&payload.status.as_str()) {
        return Err(ApiError::IncorrectStatus);
    }
    let filter = doc! {"id": appointment_id};
    let res = state
        .db
        .find_one(filter.clone(), None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    if let Some(old_appointment) = res {
        if old_appointment.status == STATUSES[1] && payload.status == STATUSES[0]
            || old_appointment.status == STATUSES[2] && payload.status == STATUSES[1]
        {
            return Err(ApiError::IncorrectStatusFlow);
        }
        state
            .db
            .update_one(filter, doc! {"$set": {"status": payload.status}}, None)
            .await
            .map_err(|_| ApiError::InternalError)?;
        Ok(StatusCode::OK)
    } else {
        Ok(StatusCode::NOT_FOUND)
    }
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct StayedCustomersInput {
    groomer_id: String,
    user_name: String,
}

async fn stayed_customers(
    state: State<SharedState>,
    Json(payload): Json<StayedCustomersInput>,
) -> Result<StatusCode, ApiError> {
    let (user_exists, groomer_exists) = tokio::join!(
        does_user_exist(&state.http, &payload.user_name),
        does_groomer_exist(&state.http, &payload.groomer_id)
    );
    if !user_exists? {
        return Err(ApiError::UserDoesNotExist);
    }
    if !groomer_exists? {
        return Err(ApiError::GroomerDoesNotExist);
    }
    let filter =
        doc! {"groomer_id": payload.groomer_id, "user_name": payload.user_name, "status": "left"};
    let mut res = state
        .db
        .find(filter, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    if res
        .try_next()
        .await
        .map_err(|_| ApiError::InternalError)?
        .is_some()
    {
        Ok(StatusCode::OK)
    } else {
        Ok(StatusCode::NOT_FOUND)
    }
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct CreateInput {
    user_name: String,
    groomer_id: String,
    pet_info: Vec<Pet>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct CreateOutput {
    id: String,
}

async fn create_appointment(
    state: State<SharedState>,
    Json(payload): Json<CreateInput>,
) -> Result<Json<CreateOutput>, ApiError> {
    let (user_exists, groomer_exists) = tokio::join!(
        does_user_exist(&state.http, &payload.user_name),
        does_groomer_exist(&state.http, &payload.groomer_id)
    );
    if !user_exists? {
        return Err(ApiError::UserDoesNotExist);
    }
    if !groomer_exists? {
        return Err(ApiError::GroomerDoesNotExist);
    }
    let payload = Appointment {
        end_date: DateTime::now(),
        groomer_id: payload.groomer_id,
        id: cuid::cuid2(),
        pets: payload.pet_info,
        start_date: DateTime::now(),
        status: String::from("awaiting"),
        user_name: payload.user_name,
    };
    state
        .db
        .insert_one(&payload, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    Ok(Json(CreateOutput { id: payload.id }))
}

#[derive(Debug)]
enum ApiError {
    InternalError,
    IncorrectStatus,
    IncorrectStatusFlow,
    UserDoesNotExist,
    GroomerDoesNotExist,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let (status, error_message) = match self {
            ApiError::InternalError => (StatusCode::INTERNAL_SERVER_ERROR, "internal server error"),
            ApiError::IncorrectStatus => (StatusCode::BAD_REQUEST, "incorrect status"),
            ApiError::IncorrectStatusFlow => (StatusCode::BAD_REQUEST, "incorrect status flow"),
            ApiError::UserDoesNotExist => (StatusCode::NOT_FOUND, "user cannot be found"),
            ApiError::GroomerDoesNotExist => (StatusCode::NOT_FOUND, "groomer cannot be found"),
        };
        let body = Json(json!({ "message": error_message }));
        (status, body).into_response()
    }
}
