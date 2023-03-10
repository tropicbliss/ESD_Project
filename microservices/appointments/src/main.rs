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
    bson::{doc, Bson, DateTime},
    options::{ClientOptions, FindOptions},
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
        client.database(&std::env::var("DATABASE").unwrap_or_else(|_| "esdproject".into()));
    let appointments_collection = database.collection::<Appointment>(
        &std::env::var("APPOINTMENTS_COLLECTION").unwrap_or_else(|_| "appointments".into()),
    );
    let capacity_collection = database.collection::<Capacity>(
        &std::env::var("CAPACITY_COLLECTION").unwrap_or_else(|_| "capacity".into()),
    );
    let shared_state = SharedState {
        appointments: appointments_collection,
        capacity: capacity_collection,
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
        .route("/checkadd", post(check_add))
        .route("/check", get(check))
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
        .post(format!("http://groomer:5000/read/{id}"))
        .json(&json!({}))
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
    appointments: Collection<Appointment>,
    capacity: Collection<Capacity>,
    http: HttpClient,
}

#[derive(Serialize, Deserialize)]
struct Appointment {
    id: String,
    user_name: String,
    groomer_id: String,
    start_date: DateTime,
    end_date: DateTime,
    status: Status,
    pets: Vec<Pet>,
}

#[derive(Serialize, Deserialize)]
struct Capacity {
    groomer_id: String,
    date: String,
    current_capacity: usize,
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
    start_date: DateTime,
    end_date: DateTime,
    groomer_picture_url: String,
    pet_names: Vec<String>,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct CheckAddInput {
    groomer_id: String,
    start_time: DateTime,
    end_time: DateTime,
    quantity: u32,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct GroomerOutput {
    capacity: usize,
}

async fn check_add(
    state: State<SharedState>,
    Json(payload): Json<CheckAddInput>,
) -> Result<StatusCode, ApiError> {
    if payload.start_time > payload.end_time {
        return Err(ApiError::StartEndDateMismatch);
    }
    let groomer = state
        .http
        .post(format!("http://groomer:5000/read/{}", payload.groomer_id))
        .json(&json!({}))
        .send()
        .await
        .map_err(|_| ApiError::InternalError)?
        .json::<GroomerOutput>()
        .await;
    let groomer_capacity = if let Ok(groomer) = groomer {
        groomer.capacity
    } else {
        return Err(ApiError::GroomerDoesNotExist);
    };
    let start_date_raw = payload.start_time.to_chrono().date_naive();
    let end_date_raw = payload.end_time.to_chrono().date_naive();
    let days: Vec<_> = start_date_raw
        .iter_days()
        .map(|day| if day == end_date_raw { None } else { Some(day) })
        .fuse()
        .flatten()
        .map(|date| date.to_string())
        .collect();
    let filter = doc! {"date": {
        "$in": &days
    }, "groomer_id": &payload.groomer_id};
    let res = state
        .capacity
        .find(filter.clone(), None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::InternalError)?;
    for capacity in res {
        if capacity.current_capacity + payload.quantity as usize > groomer_capacity {
            return Err(ApiError::OverCapacity);
        }
    }
    let update = doc! {"current_capacity": payload.quantity as i64};
    state
        .capacity
        .update_many(filter, update, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    Ok(StatusCode::ACCEPTED)
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct CapacityInfoOutput {
    date: String,
    remaining_capacity: usize,
}

async fn check(
    state: State<SharedState>,
    Path(groomer_id): Path<String>,
) -> Result<Json<Vec<CapacityInfoOutput>>, ApiError> {
    let groomer = state
        .http
        .post(format!("http://groomer:5000/read/{}", groomer_id))
        .json(&json!({}))
        .send()
        .await
        .map_err(|_| ApiError::InternalError)?
        .json::<GroomerOutput>()
        .await;
    let groomer_capacity = if let Ok(groomer) = groomer {
        groomer.capacity
    } else {
        return Err(ApiError::GroomerDoesNotExist);
    };
    let filter = doc! {"date": {
        "$gte": DateTime::now()
    }, "groomer_id": groomer_id};
    let res = state
        .capacity
        .find(filter, FindOptions::builder().limit(27).build())
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res: Vec<_> = res
        .into_iter()
        .map(|cap| CapacityInfoOutput {
            remaining_capacity: groomer_capacity - cap.current_capacity,
            date: cap.date,
        })
        .collect();
    Ok(Json(res))
}

async fn get_user(
    Path(user_name): Path<String>,
    state: State<SharedState>,
) -> Result<Json<Vec<UserEndpointOutput>>, ApiError> {
    #[derive(Deserialize)]
    #[serde(rename_all = "camelCase")]
    struct UserReadEndpointOutput {
        name: String,
        picture_url: String,
    }

    if !does_user_exist(&state.http, &user_name).await? {
        return Err(ApiError::UserDoesNotExist);
    }
    let filter = doc! {"user_name": user_name};
    let res = state
        .appointments
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
            end_date: app.end_date,
            groomer_name: groomer_info.get(&app.groomer_id).unwrap().name.clone(),
            groomer_picture_url: groomer_info
                .get(&app.groomer_id)
                .unwrap()
                .picture_url
                .clone(),
            groomer_id: app.groomer_id,
            pet_names: app.pets.into_iter().map(|pet| pet.name).collect(),
            start_date: app.start_date,
        })
        .collect();
    Ok(Json(res))
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct SignInOutput {
    id: String,
    user_name: String,
    start_date: DateTime,
    end_date: DateTime,
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
        .appointments
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
                    end_date: app.end_date,
                    id: app.id,
                    pets: app.pets,
                    start_date: app.start_date,
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
        .appointments
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
                    end_date: app.end_date,
                    id: app.id,
                    pets: app.pets,
                    start_date: app.start_date,
                    user_name: res.name,
                }
            }
        })
        .buffer_unordered(3)
        .collect()
        .await;
    Ok(Json(res))
}

#[derive(Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "lowercase")]
enum Status {
    Awaiting,
    Staying,
    Left,
}

impl From<Status> for Bson {
    fn from(value: Status) -> Self {
        let string = match value {
            Status::Awaiting => "awaiting",
            Status::Left => "left",
            Status::Staying => "staying",
        };
        Self::String(string.to_string())
    }
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct StatusChangeInput {
    status: Status,
}

async fn change_appointment_status(
    Path(appointment_id): Path<String>,
    state: State<SharedState>,
    Json(payload): Json<StatusChangeInput>,
) -> Result<StatusCode, ApiError> {
    let filter = doc! {"id": appointment_id};
    let res = state
        .appointments
        .find_one(filter.clone(), None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    if let Some(old_appointment) = res {
        if old_appointment.status == Status::Staying && payload.status == Status::Awaiting
            || old_appointment.status == Status::Left && payload.status == Status::Staying
        {
            return Err(ApiError::IncorrectStatusFlow);
        }
        state
            .appointments
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
        .appointments
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
        status: Status::Awaiting,
        user_name: payload.user_name,
    };
    state
        .appointments
        .insert_one(&payload, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    Ok(Json(CreateOutput { id: payload.id }))
}

#[derive(Debug)]
enum ApiError {
    InternalError,
    IncorrectStatusFlow,
    UserDoesNotExist,
    GroomerDoesNotExist,
    StartEndDateMismatch,
    OverCapacity,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let (status, error_message) = match self {
            ApiError::InternalError => (StatusCode::INTERNAL_SERVER_ERROR, "internal server error"),
            ApiError::IncorrectStatusFlow => (StatusCode::BAD_REQUEST, "incorrect status flow"),
            ApiError::UserDoesNotExist => (StatusCode::NOT_FOUND, "user cannot be found"),
            ApiError::GroomerDoesNotExist => (StatusCode::NOT_FOUND, "groomer cannot be found"),
            ApiError::StartEndDateMismatch => (
                StatusCode::BAD_REQUEST,
                "the end date is earlier than the start date",
            ),
            ApiError::OverCapacity => (StatusCode::NOT_FOUND, "one or multiple dates at capacity"),
        };
        let body = Json(json!({ "message": error_message }));
        (status, body).into_response()
    }
}
