use anyhow::Result;
use async_graphql::{http::GraphiQLSource, Context, EmptySubscription, Object, Schema, ID};
use async_graphql_axum::{GraphQLRequest, GraphQLResponse};
use axum::{
    extract::State,
    response::{Html, IntoResponse},
    routing::get,
    Router,
};
use mongodb::{
    bson::{doc, Document},
    options::ClientOptions,
    Client, Collection,
};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use thiserror::Error;
use tracing_subscriber::{prelude::__tracing_subscriber_SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "user=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();
    let client_options = ClientOptions::parse(&std::env::var("DB_URI")?).await?;
    let client = Client::with_options(client_options)?;
    let database = client.database(&std::env::var("DATABASE").unwrap_or_else(|_| "user".into()));
    let collection =
        database.collection::<User>(&std::env::var("COLLECTION").unwrap_or_else(|_| "user".into()));
    let schema = Schema::build(QueryRoot, MutationRoot, EmptySubscription)
        .data(collection)
        .finish();
    let app = Router::new()
        .route("/", get(graphiql).post(graphql_handler))
        .with_state(schema);
    let addr = std::env::var("ADDR").unwrap_or_else(|_| "127.0.0.1:3000".into());
    let addr: SocketAddr = addr.parse()?;
    tracing::debug!("listening on {addr}");
    tracing::debug!("GraphiQL IDE: {addr}");
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await?;
    Ok(())
}

#[derive(Deserialize, Serialize)]
struct User {
    name: String,
    contact_no: String,
    email: String,
}

#[Object]
impl User {
    async fn name(&self) -> &str {
        &self.name
    }

    async fn contact_no(&self) -> &str {
        &self.contact_no
    }

    async fn email(&self) -> &str {
        &self.email
    }
}

type UserSchema = Schema<QueryRoot, MutationRoot, EmptySubscription>;

struct QueryRoot;

#[Object]
impl QueryRoot {
    async fn get_user(
        &self,
        ctx: &Context<'_>,
        name: String,
    ) -> async_graphql::Result<Option<User>> {
        let filter = doc! {"name": name};
        Ok(ctx
            .data_unchecked::<Collection<User>>()
            .find_one(filter, None)
            .await?)
    }
}

struct MutationRoot;

#[Object]
impl MutationRoot {
    async fn create_user(
        &self,
        ctx: &Context<'_>,
        name: String,
        contact_no: String,
        email: String,
    ) -> async_graphql::Result<ID> {
        let is_valid_phone = validator::validate_phone(&contact_no);
        let is_valid_email = validator::validate_email(&email);
        if !is_valid_email {
            return Err(ApiError::EmailValidation.into());
        }
        if !is_valid_phone {
            return Err(ApiError::ContactNoValidation.into());
        }
        let user_exists = ctx
            .data_unchecked::<Collection<User>>()
            .find_one(doc! {"name": name}, None)
            .await?
            .is_some();
        if user_exists {
            return Err(ApiError::UserExists);
        }
        let payload = User {
            contact_no,
            email,
            name,
        };
        ctx.data_unchecked::<Collection<User>>()
            .insert_one(&payload, None)
            .await?;
        Ok(ID(payload.name))
    }

    async fn update_user(
        &self,
        ctx: &Context<'_>,
        name: Option<String>,
        contact_no: Option<String>,
        email: Option<String>,
    ) -> Result<bool> {
        let query = doc! {"name": name};
        let mut update = Document::new();
        if let Some(contact_no) = &contact_no {
            if !validator::validate_phone(contact_no) {
                return Err(ApiError::ContactNoValidation.into());
            }
            update.insert("contact_no", contact_no);
        }
        if let Some(email) = &email {
            if !validator::validate_email(email) {
                return Err(ApiError::EmailValidation.into());
            }
            update.insert("email", email);
        }
        let update_final = doc! {"$set": update};
        ctx.data_unchecked::<Collection<User>>()
            .update_one(query, update_final, None)
            .await?;
        Ok(true)
    }
}

async fn graphql_handler(state: State<UserSchema>, req: GraphQLRequest) -> GraphQLResponse {
    state.execute(req.into_inner()).await.into()
}

async fn graphiql() -> impl IntoResponse {
    Html(GraphiQLSource::build().endpoint("/").finish())
}

#[derive(Error, Debug)]
enum ApiError {
    #[error("contact number provided is invalid")]
    ContactNoValidation,
    #[error("email provided is invalid")]
    EmailValidation,
    #[error("user already exists")]
    UserExists,
}
