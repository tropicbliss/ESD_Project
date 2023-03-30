# Instructions

## Installation

1. Clone this repo.
2. Navigate to the `microservices` folder.
3. Run `docker compose build`.
4. This step will take a while (up to 10 minutes).
5. Run `docker compose up -d`.
6. Go to `http://localhost:5000/docs` for documentation.

## Exposed ports

- `5000`: Main orchestrator
- `5001`: Stripe microservice
- `15672`: RabbitMQ admin panel
- `1337`: Konga
- `8000`: Kong
