# Stage 1: Builder - Build the application and dependencies
FROM python:3.14-alpine AS builder

# Install system build dependencies
RUN apk add --no-cache build-base postgresql-dev

# Install Poetry
RUN pip install poetry

# Set up Poetry
WORKDIR /app
RUN poetry config virtualenvs.in-project true

# Copy project files
COPY poetry.lock pyproject.toml ./
COPY scheduler_service ./scheduler_service

# Install dependencies, including the project itself in editable mode
# This creates a venv inside /app/.venv
RUN poetry install --without dev


# Stage 2: Runner - Create the final lightweight image
FROM python:3.14-alpine AS runner

# Install only runtime system dependencies
RUN apk add --no-cache libpq

# Create a non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

WORKDIR /home/appuser/app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /home/appuser/app/.venv

# Make the venv available in the path
ENV PATH="/home/appuser/app/.venv/bin:$PATH"

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["scheduler", "runserver", "--host", "0.0.0.0", "--port", "8000", "--no-debug"]
