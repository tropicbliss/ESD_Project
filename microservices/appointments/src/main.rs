use anyhow::Result;
use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{delete, get, post},
    Json, Router,
};
use futures::{stream, StreamExt, TryStreamExt};
use graphql_client::{GraphQLQuery, Response};
use mongodb::{
    bson::{doc, Bson, DateTime},
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
        client.database(&std::env::var("DATABASE").unwrap_or_else(|_| "esdproject".into()));
    let appointments_collection = database.collection::<Appointment>(
        &std::env::var("APPOINTMENTS_COLLECTION").unwrap_or_else(|_| "appointments".into()),
    );
    let shared_state = SharedState {
        appointments: appointments_collection,
        http: HttpClient::builder()
            .timeout(Duration::from_secs(9))
            .build()?,
    };
    let app = Router::new()
        .route("/user/:id", get(get_user))
        .route("/signin/:id", get(get_arriving_customers))
        .route("/staying/:id", get(get_staying_customers))
        .route("/status/:id", post(change_appointment_status))
        .route("/create", post(create_appointment))
        .route("/stayed", post(stayed_customers))
        .route("/quantity", post(get_quantity))
        .route("/get/:id", post(get_appointments_in_month))
        .route("/update/:id", post(update_appointment_date))
        .route("/transaction/:id", get(get_appointment))
        .route("/delete/:id", delete(delete_appointment))
        .route("/groomer/:id", get(get_all_groomer_appointments))
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

#[derive(Clone)]
struct SharedState {
    appointments: Collection<Appointment>,
    http: HttpClient,
}

#[derive(Serialize, Deserialize)]
struct Appointment {
    id: String,
    user_name: String,
    groomer_name: String,
    start_date: DateTime,
    end_date: DateTime,
    status: Status,
    pets: Vec<Pet>,
    total_price: f64,
    price_tier: String,
    transaction_id: String,
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
    groomer_name: String,
    start_date: String,
    end_date: String,
    groomer_picture_url: String,
    pet_names: Vec<String>,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct CheckAddInput {
    start_time: String,
    end_time: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct CheckAddOutput {
    day_length: usize,
}

async fn get_quantity(
    Json(payload): Json<CheckAddInput>,
) -> Result<Json<CheckAddOutput>, ApiError> {
    if payload.start_time > payload.end_time {
        return Err(ApiError::StartEndDateMismatch);
    }
    let start_date_raw = DateTime::parse_rfc3339_str(payload.start_time)
        .map_err(|_| ApiError::IncorrectTimeFormat)?
        .to_chrono()
        .date_naive();
    let end_date_raw = DateTime::parse_rfc3339_str(payload.end_time)
        .map_err(|_| ApiError::IncorrectTimeFormat)?
        .to_chrono()
        .date_naive();
    let days = start_date_raw
        .iter_days()
        .map(|day| if day >= end_date_raw { None } else { Some(day) })
        .fuse()
        .flatten()
        .count();
    Ok(Json(CheckAddOutput { day_length: days }))
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RefundOutput {
    transaction_id: String,
}

async fn get_appointment(
    Path(appointment_id): Path<String>,
    state: State<SharedState>,
) -> Result<Json<RefundOutput>, ApiError> {
    let user = state
        .appointments
        .find_one(doc! {"id": appointment_id}, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    if let Some(user) = user {
        Ok(Json(RefundOutput {
            transaction_id: user.transaction_id,
        }))
    } else {
        Err(ApiError::AppointmentDoesNotExist)
    }
}

async fn delete_appointment(
    Path(appointment_id): Path<String>,
    state: State<SharedState>,
) -> Result<StatusCode, ApiError> {
    let user = state
        .appointments
        .delete_one(doc! {"id": appointment_id}, None)
        .await
        .map_err(|e| e.kind)
        .map_err(|_| ApiError::InternalError)?;
    if user.deleted_count == 0 {
        Err(ApiError::AppointmentDoesNotExist)
    } else {
        Ok(StatusCode::OK)
    }
}

async fn get_all_groomer_appointments(
    Path(groomer_name): Path<String>,
    state: State<SharedState>,
) -> Result<Json<Vec<SignInOutput>>, ApiError> {
    if !does_groomer_exist(&state.http, &groomer_name).await? {
        return Err(ApiError::GroomerDoesNotExist);
    }
    let filter = doc! {
        "groomer_name": groomer_name
    };
    let res = state
        .appointments
        .find(filter, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res = res
        .into_iter()
        .map(|app| {
            let pets = app
                .pets
                .into_iter()
                .map(|e| e.try_into())
                .collect::<Result<Vec<_>, _>>()
                .unwrap();
            SignInOutput {
                end_date: app.end_date.try_to_rfc3339_string().unwrap(),
                id: app.id,
                pets,
                start_date: app.start_date.try_to_rfc3339_string().unwrap(),
                user_name: app.user_name,
                total_price: app.total_price,
                price_tier: app.price_tier,
            }
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
    let groomers: HashSet<String> = res.iter().map(|app| app.groomer_name.clone()).collect();
    let groomer_info: HashMap<String, UserReadEndpointOutput> = stream::iter(groomers)
        .map(|name| {
            let client = &state.http;
            async move {
                let res: UserReadEndpointOutput = client
                    .get(format!("http://groomer:5000/search/name/{}", name))
                    .send()
                    .await
                    .unwrap()
                    .json()
                    .await
                    .unwrap();
                (name, res)
            }
        })
        .buffer_unordered(3)
        .collect()
        .await;
    let res = res
        .into_iter()
        .map(|app| UserEndpointOutput {
            end_date: app.end_date.try_to_rfc3339_string().unwrap(),
            groomer_name: groomer_info.get(&app.groomer_name).unwrap().name.clone(),
            groomer_picture_url: groomer_info
                .get(&app.groomer_name)
                .unwrap()
                .picture_url
                .clone(),
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
    pets: Vec<PetInputOutput>,
    price_tier: String,
    total_price: f64,
}

#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct PetInputOutput {
    pet_type: PetType,
    name: String,
    gender: PetGender,
    age: usize,
    medical_info: String,
}

#[derive(Serialize, Deserialize)]
enum PetType {
    Birds,
    Hamsters,
    Cats,
    Dogs,
    Rabbits,
    GuineaPigs,
    Chinchillas,
    Mice,
    Fishes,
}

#[derive(Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
enum PetGender {
    Male,
    Female,
    Unspecified,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct MonthYearInput {
    month: u32,
    year: u32,
}

async fn get_appointments_in_month(
    Path(groomer_name): Path<String>,
    state: State<SharedState>,
    Json(payload): Json<MonthYearInput>,
) -> Result<Json<Vec<SignInOutput>>, ApiError> {
    if !does_groomer_exist(&state.http, &groomer_name).await? {
        return Err(ApiError::GroomerDoesNotExist);
    }
    let filter = doc! {
        "$expr": {
            "$and": [
                {
                    "$eq": [
                        {
                            "$month": "$end_date"
                        },
                        payload.month
                    ]
                },
                {
                    "$eq": [
                        {
                            "$year": "$end_date"
                        },
                        payload.year
                    ]
                },
                {
                    "groomer_name": groomer_name
                }
            ]
        }
    };
    let res = state
        .appointments
        .find(filter, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res = res
        .into_iter()
        .map(|app| {
            let pets = app
                .pets
                .into_iter()
                .map(|e| e.try_into())
                .collect::<Result<Vec<_>, _>>()
                .unwrap();
            SignInOutput {
                end_date: app.end_date.try_to_rfc3339_string().unwrap(),
                id: app.id,
                pets,
                start_date: app.start_date.try_to_rfc3339_string().unwrap(),
                user_name: app.user_name,
                total_price: app.total_price,
                price_tier: app.price_tier,
            }
        })
        .collect();
    Ok(Json(res))
}

async fn get_arriving_customers(
    Path(groomer_name): Path<String>,
    state: State<SharedState>,
) -> Result<Json<Vec<SignInOutput>>, ApiError> {
    if !does_groomer_exist(&state.http, &groomer_name).await? {
        return Err(ApiError::GroomerDoesNotExist);
    }
    let filter = doc! {"groomer_name": groomer_name, "status": "awaiting"};
    let res = state
        .appointments
        .find(filter, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res = res
        .into_iter()
        .map(|app| {
            let pets = app
                .pets
                .into_iter()
                .map(|e| e.try_into())
                .collect::<Result<Vec<_>, _>>()
                .unwrap();
            SignInOutput {
                end_date: app.end_date.try_to_rfc3339_string().unwrap(),
                id: app.id,
                pets,
                start_date: app.start_date.try_to_rfc3339_string().unwrap(),
                user_name: app.user_name,
                total_price: app.total_price,
                price_tier: app.price_tier,
            }
        })
        .collect();
    Ok(Json(res))
}

#[derive(Deserialize)]
struct UpdateInput {
    start_date: String,
    end_date: String,
}

async fn update_appointment_date(
    Path(groomer_name): Path<String>,
    state: State<SharedState>,
    Json(payload): Json<UpdateInput>,
) -> Result<StatusCode, ApiError> {
    let start_date = DateTime::parse_rfc3339_str(payload.start_date)
        .map_err(|_| ApiError::IncorrectTimeFormat)?;
    let end_date =
        DateTime::parse_rfc3339_str(payload.end_date).map_err(|_| ApiError::IncorrectTimeFormat)?;
    if !does_groomer_exist(&state.http, &groomer_name).await? {
        return Err(ApiError::GroomerDoesNotExist);
    }
    let filter = doc! {"groomer_name": groomer_name, "status": "awaiting"};
    let res = state
        .appointments
        .find_one_and_update(
            filter,
            doc! {"$set": {"start_date": start_date, "end_date": end_date}},
            None,
        )
        .await
        .map_err(|_| ApiError::InternalError)?;
    if res.is_some() {
        Ok(StatusCode::OK)
    } else {
        Err(ApiError::AppointmentDoesNotExist)
    }
}

async fn get_staying_customers(
    Path(groomer_name): Path<String>,
    state: State<SharedState>,
) -> Result<Json<Vec<SignInOutput>>, ApiError> {
    if !does_groomer_exist(&state.http, &groomer_name).await? {
        return Err(ApiError::GroomerDoesNotExist);
    }
    let filter = doc! {"groomer_name": groomer_name, "status": "staying"};
    let res = state
        .appointments
        .find(filter, None)
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res: Vec<_> = res
        .try_collect()
        .await
        .map_err(|_| ApiError::InternalError)?;
    let res = res
        .into_iter()
        .map(|app| {
            let pets = app
                .pets
                .into_iter()
                .map(|e| e.try_into())
                .collect::<Result<Vec<_>, _>>()
                .unwrap();
            SignInOutput {
                end_date: app.end_date.try_to_rfc3339_string().unwrap(),
                id: app.id,
                pets,
                start_date: app.start_date.try_to_rfc3339_string().unwrap(),
                user_name: app.user_name,
                total_price: app.total_price,
                price_tier: app.price_tier,
            }
        })
        .collect();
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
        Err(ApiError::AppointmentDoesNotExist)
    }
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct StayedCustomersInput {
    groomer_name: String,
    user_name: String,
}

async fn stayed_customers(
    state: State<SharedState>,
    Json(payload): Json<StayedCustomersInput>,
) -> Result<StatusCode, ApiError> {
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
    let filter = doc! {"groomer_name": payload.groomer_name, "user_name": payload.user_name, "status": "left"};
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
        Err(ApiError::AppointmentDoesNotExist)
    }
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct CreateInput {
    user_name: String,
    groomer_name: String,
    pet_info: Vec<PetInputOutput>,
    price_tier: String,
    total_price: f64,
    start_time: String,
    end_time: String,
    transaction_id: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct CreateOutput {
    id: String,
}

impl TryFrom<Pet> for PetInputOutput {
    type Error = &'static str;

    fn try_from(value: Pet) -> std::result::Result<Self, Self::Error> {
        let gender = match value.gender.as_str() {
            "male" => PetGender::Male,
            "female" => PetGender::Female,
            "unspecified" => PetGender::Unspecified,
            _ => return Err("unknown pet gender"),
        };
        let pet_type = match value.pet_type.as_str() {
            "Birds" => PetType::Birds,
            "Cats" => PetType::Cats,
            "Chinchillas" => PetType::Chinchillas,
            "Dogs" => PetType::Dogs,
            "Fishes" => PetType::Fishes,
            "GuineaPigs" => PetType::GuineaPigs,
            "Hamsters" => PetType::Hamsters,
            "Mice" => PetType::Mice,
            "Rabbits" => PetType::Rabbits,
            _ => return Err("unknown pet type"),
        };
        Ok(Self {
            age: value.age,
            gender,
            medical_info: value.medical_info,
            name: value.name,
            pet_type,
        })
    }
}

impl From<PetInputOutput> for Pet {
    fn from(value: PetInputOutput) -> Self {
        let gender = match value.gender {
            PetGender::Female => "female",
            PetGender::Male => "male",
            PetGender::Unspecified => "unspecified",
        }
        .to_string();
        let pet_type = match value.pet_type {
            PetType::Birds => "Birds",
            PetType::Cats => "Cats",
            PetType::Chinchillas => "Chinchillas",
            PetType::Dogs => "Dogs",
            PetType::Fishes => "Fishes",
            PetType::GuineaPigs => "GuineaPigs",
            PetType::Hamsters => "Hamsters",
            PetType::Mice => "Mice",
            PetType::Rabbits => "Rabbits",
        }
        .to_string();
        Self {
            age: value.age,
            gender,
            medical_info: value.medical_info,
            name: value.name,
            pet_type,
        }
    }
}

async fn create_appointment(
    state: State<SharedState>,
    Json(payload): Json<CreateInput>,
) -> Result<Json<CreateOutput>, ApiError> {
    let start_time = DateTime::parse_rfc3339_str(payload.start_time)
        .map_err(|_| ApiError::IncorrectTimeFormat)?;
    let end_time =
        DateTime::parse_rfc3339_str(payload.end_time).map_err(|_| ApiError::IncorrectTimeFormat)?;
    if start_time > end_time {
        return Err(ApiError::StartEndDateMismatch);
    }
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
    let payload = Appointment {
        end_date: end_time,
        groomer_name: payload.groomer_name,
        id: cuid::cuid2(),
        pets: payload.pet_info.into_iter().map(|e| e.into()).collect(),
        start_date: start_time,
        status: Status::Awaiting,
        user_name: payload.user_name,
        total_price: payload.total_price,
        price_tier: payload.price_tier,
        transaction_id: payload.transaction_id,
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
    AppointmentDoesNotExist,
    IncorrectTimeFormat,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        let (status, error_message) = match self {
            ApiError::InternalError => (StatusCode::INTERNAL_SERVER_ERROR, "internal server error"),
            ApiError::IncorrectStatusFlow => (StatusCode::BAD_REQUEST, "incorrect status flow"),
            ApiError::UserDoesNotExist => (StatusCode::NOT_FOUND, "user cannot be found"),
            ApiError::GroomerDoesNotExist => (StatusCode::NOT_FOUND, "groomer cannot be found"),
            ApiError::AppointmentDoesNotExist => {
                (StatusCode::NOT_FOUND, "appointment cannot be found")
            }
            ApiError::StartEndDateMismatch => (
                StatusCode::BAD_REQUEST,
                "the end date is earlier than the start date",
            ),
            ApiError::IncorrectTimeFormat => (StatusCode::BAD_REQUEST, "incorrect time format"),
        };
        let body = Json(json!({ "message": error_message }));
        (status, body).into_response()
    }
}
