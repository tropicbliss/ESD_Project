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
use uuid::Uuid;

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
    let database = client.database("appointments");
    let collection = database.collection::<Appointment>("appointments");
    let app = Router::new()
        .route("/user/:id", get(get_user))
        .route("/signin/:id", get(get_arriving_customers))
        .route("/signout/:id", get(get_leaving_customers))
        .route("/staying/:id", get(get_staying_customers))
        .route("/status/:id", post(change_appointment_status))
        .route("/create", post(create_appointment))
        .route("/stayed", post(stayed_customers))
        .with_state(collection);
    let addr = std::env::var("ADDR").unwrap_or_else(|_| "127.0.0.1:3000".into());
    let addr: SocketAddr = addr.parse()?;
    tracing::debug!("listening on {addr}");
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await?;
    Ok(())
}

macro_rules! today_date {
    () => {
        chrono::offset::Local::now().date_naive().to_string()
    };
}

#[derive(Serialize, Deserialize)]
struct Appointment {
    id: String,
    user_id: String,
    groomer_id: String,
    start_date: String,
    end_date: String,
    status: String,
    pets: Vec<Pet>,
}

#[derive(Serialize, Deserialize)]
struct AppointmentInput {
    user_id: String,
    groomer_id: String,
    start_date: String,
    end_date: String,
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

async fn get_user(
    Path(user_id): Path<String>,
    state: State<Collection<Appointment>>,
) -> Result<Json<Vec<Appointment>>, ApiError> {
    let filter = doc! {"user_id": user_id};
    let res = state
        .find(filter, None)
        .await
        .map_err(|_| ApiError::DatabaseError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::DatabaseError)?;
    Ok(Json(res))
}

async fn get_arriving_customers(
    Path(groomer_id): Path<String>,
    state: State<Collection<Appointment>>,
) -> Result<Json<Vec<Appointment>>, ApiError> {
    let filter = doc! {"groomer_id": groomer_id, "status": "awaiting", "start_date": today_date!()};
    let res = state
        .find(filter, None)
        .await
        .map_err(|_| ApiError::DatabaseError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::DatabaseError)?;
    Ok(Json(res))
}

async fn get_leaving_customers(
    Path(groomer_id): Path<String>,
    state: State<Collection<Appointment>>,
) -> Result<Json<Vec<Appointment>>, ApiError> {
    let filter = doc! {"groomer_id": groomer_id, "status": "staying", "end_date": today_date!()};
    let res = state
        .find(filter, None)
        .await
        .map_err(|_| ApiError::DatabaseError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::DatabaseError)?;
    Ok(Json(res))
}

async fn get_staying_customers(
    Path(groomer_id): Path<String>,
    state: State<Collection<Appointment>>,
) -> Result<Json<Vec<Appointment>>, ApiError> {
    let filter = doc! {"groomer_id": groomer_id, "status": "staying"};
    let res = state
        .find(filter, None)
        .await
        .map_err(|_| ApiError::DatabaseError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::DatabaseError)?;
    Ok(Json(res))
}

#[derive(Serialize, Deserialize)]
struct StayedCustomersInput {
    groomer_id: String,
    user_id: String,
}

async fn stayed_customers(
    state: State<Collection<Appointment>>,
    Json(payload): Json<StayedCustomersInput>,
) -> Result<Json<Vec<Appointment>>, ApiError> {
    let filter =
        doc! {"groomer_id": payload.groomer_id, "user_id": payload.user_id, "status": "left"};
    let res = state
        .find(filter, None)
        .await
        .map_err(|_| ApiError::DatabaseError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::DatabaseError)?;
    Ok(Json(res))
}

#[derive(Serialize, Deserialize)]
struct AppointmentStatus {
    status: String,
}

const STATUSES: [&'static str; 3] = ["awaiting", "staying", "left"];

async fn change_appointment_status(
    Path(appointment_id): Path<String>,
    state: State<Collection<Appointment>>,
    Json(payload): Json<AppointmentStatus>,
) -> Result<StatusCode, ApiError> {
    if !STATUSES.contains(&payload.status.as_str()) {
        return Err(ApiError::IncorrectStatus);
    }
    let filter = doc! {"id": appointment_id};
    let res = state
        .find_one(filter.clone(), None)
        .await
        .map_err(|_| ApiError::DatabaseError)?;
    if let Some(old_appointment) = res {
        if old_appointment.status == STATUSES[1] && payload.status == STATUSES[0]
            || old_appointment.status == STATUSES[2] && payload.status == STATUSES[1]
        {
            return Err(ApiError::IncorrectStatusFlow);
        }
        state
            .update_one(filter, doc! {"$set": {"status": payload.status}}, None)
            .await
            .map_err(|_| ApiError::DatabaseError)?;
        Ok(StatusCode::OK)
    } else {
        Ok(StatusCode::NOT_FOUND)
    }
}

async fn create_appointment(
    state: State<Collection<Appointment>>,
    Json(payload): Json<AppointmentInput>,
) -> Result<Json<Appointment>, ApiError> {
    let payload = Appointment {
        end_date: payload.end_date,
        groomer_id: payload.groomer_id,
        id: Uuid::new_v4().to_string(),
        pets: payload.pets,
        start_date: payload.start_date,
        status: String::from("awaiting"),
        user_id: payload.user_id,
    };
    state.insert_one(&payload, None).await.unwrap();
    Ok(Json(payload))
}

#[derive(Debug)]
enum ApiError {
    DatabaseError,
    IncorrectStatus,
    IncorrectStatusFlow,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let (status, error_message) = match self {
            ApiError::DatabaseError => {
                (StatusCode::INTERNAL_SERVER_ERROR, "error querying database")
            }
            ApiError::IncorrectStatus => (StatusCode::BAD_REQUEST, "incorrect status"),
            ApiError::IncorrectStatusFlow => (StatusCode::BAD_REQUEST, "incorrect status flow"),
        };
        let body = Json(json!({ "error": error_message }));
        (status, body).into_response()
    }
}
