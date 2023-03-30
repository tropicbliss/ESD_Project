# Instructions

## Installation

1. Clone this repo.
2. Navigate to the `microservices` folder.
3. Run `docker compose build`.
4. This step will take a while (up to 10 minutes).
5. Run `docker compose up -d`.
6. Navigate to `http://localhost:1337` and sign up for an account.
7. Log in, and setup a connection with `default` as the name and `http://kong:8001` as the Kong Admin URL.
8. Click "Snapshots" on the left panel.
9. Click on "Import from file", and import `snapshot.json` from the respository's root directory.
10. Click on "details", and click "restore".
11. Go to `http://localhost:8000/backend/docs` for documentation, and `http://localhost:8000` for the frontend homepage.

## Exposed ports

- `15672`: RabbitMQ admin panel
- `1337`: Konga
- `8000`: Everything that is not an admin panel
