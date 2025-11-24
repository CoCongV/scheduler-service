# Stage 1: Builder
# This stage installs build dependencies, creates a virtual environment, and builds the wheels.
FROM python:3.14-alpine AS builder

# Install poetry
RUN pip install poetry

# Install build dependencies for Python packages
# build-base is for C extensions, postgresql-dev for asyncpg
RUN apk add --no-cache build-base postgresql-dev

# Set up a virtual environment that will be copied to the runner
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set Poetry config to not create a virtual env inside the project
RUN poetry config virtualenvs.create false

# Copy project files
WORKDIR /app
COPY poetry.lock pyproject.toml ./

# Install dependencies into the virtual environment
RUN poetry install --without dev --no-root

# Copy the application source code
COPY scheduler_service ./scheduler_service

# Build the wheel
RUN poetry build


# Stage 2: Runner
# This stage creates the final lightweight image
FROM python:3.14-alpine AS runner

# Install only runtime dependencies
RUN apk add --no-cache libpq

# Create a non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set home directory for the new user
ENV HOME=/home/appuser
WORKDIR $HOME/app

# Copy the built wheel from the builder stage
COPY --from=builder /app/dist/*.whl .

# Copy the virtual environment from the builder stage
# Ensure the new user owns this directory
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Install the application wheel into the virtual environment
RUN /opt/venv/bin/pip install --no-cache-dir *.whl && \
    rm -f *.whl

# Make the venv available in the path for the appuser
ENV PATH="/opt/venv/bin:$PATH"
USER appuser

# Expose the port
EXPOSE 8000

# Command to run the application
# Use the scheduler CLI tool, as it's the standard way for this project
CMD ["scheduler", "runserver", "--host", "0.0.0.0", "--port", "8000", "--no-debug"]
