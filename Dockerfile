# Stage 1: Builder - Build the application and dependencies
FROM python:3.14-alpine AS builder

# Install system build dependencies
RUN apk add --no-cache build-base postgresql-dev

# Install Poetry
RUN pip install poetry

# Set up Poetry to create the venv in the project directory
WORKDIR /app
RUN poetry config virtualenvs.in-project true

# Copy project definition and source code
COPY poetry.lock pyproject.toml ./
COPY scheduler_service ./scheduler_service

# Install dependencies, creating the .venv directory
RUN poetry install --without dev


# Stage 2: Runner - Create the final lightweight image
FROM python:3.14-alpine AS runner

# Install only runtime system dependencies
RUN apk add --no-cache libpq

# Create a non-root user and its home directory
RUN addgroup -S appgroup && adduser -S -h /home/appuser -G appgroup appuser

# Set up the application directory and change ownership
WORKDIR /home/appuser/app
RUN chown appuser:appgroup /home/appuser/app

# Copy the virtual environment from the builder stage and set ownership
COPY --from=builder --chown=appuser:appgroup /app/.venv /home/appuser/app/.venv

# Switch to the non-root user
USER appuser

# Make the venv available in the path
ENV PATH="/home/appuser/app/.venv/bin:$PATH"

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["scheduler", "runserver", "--host", "0.0.0.0", "--port", "8000", "--no-debug"]
