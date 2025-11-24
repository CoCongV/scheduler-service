# Scheduler Service

[![Build Status](https://travis-ci.org/FX-HAO/scheduler-service.svg?branch=develop)](https://travis-ci.org/FX-HAO/scheduler-service)
[![codecov](https://codecov.io/github/CoCongV/scheduler-service/graph/badge.svg?token=tvuEjqNQss)](https://codecov.io/github/CoCongV/scheduler-service)
[![codebeat badge](https://codebeat.co/badges/bc50f26a-7be4-4b19-a4bd-b83d505765e3)](https://codebeat.co/projects/github-com-fx-hao-scheduler-service)
[![](https://images.microbadger.com/badges/image/fuxin/scheduler-service.svg)](https://microbadger.com/images/fuxin/scheduler-service "Get your own image badge on microbadger.com")

This is a project for providing service based on REST to schedule tasks.
With this you can trigger an action every day of the month, every day of the week or every single day.
You can also select the hour of the day. If you're a developer, this is similar to a crontab, cronjob or cron.

## Tech Stack

- **Web Framework**: FastAPI
- **ORM**: Tortoise-ORM (PostgreSQL)
- **Task Queue**: Dramatiq (RabbitMQ)
- **Package Manager**: Poetry

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.14+
- Poetry

### 1. Start Infrastructure

Start PostgreSQL and RabbitMQ using Docker:

```bash
# Start RabbitMQ
docker run -d --hostname my-rabbit --name some-rabbit -p 5672:5672 -p 15672:15672 rabbitmq:4-management

# Start PostgreSQL
docker run -d --name some-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:latest
```

### 2. Configuration

The application uses `config.toml` in the project root directory for configuration.

Create a `config.toml` with the following content:

```toml
PG_URL = "postgresql://postgres:postgres@localhost:5432/scheduler"
DRAMATIQ_URL = "amqp://guest:guest@localhost:5672/%2F"
SECRET_KEY = "your-secret-key"
```

### 3. Install Dependencies

```bash
poetry install
```

### 4. Run Application

The project includes a convenient CLI tool `scheduler`.

```bash
# Initialize database (create tables)
poetry run scheduler init-db

# Start the web server
poetry run scheduler runserver

# Start the task worker (in a separate terminal)
poetry run scheduler worker
```

## Testing

Run the test suite with coverage:

```bash
poetry run scheduler test --coverage
```

## Roadmap

- [x] User login required
- [x] Asynchronous tasks (via Dramatiq)
- [x] Continuous integration and deployment
- [x] Deploy with docker