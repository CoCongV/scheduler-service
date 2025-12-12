# Stage 1: Frontend Builder
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npm run build


# Stage 2: Backend Builder - Build the application and dependencies
FROM python:3.14-alpine AS builder

# Install system build dependencies
RUN apk add --no-cache build-base

# Install Poetry
RUN pip install poetry

# Set up workdir
WORKDIR /app

# Copy project definition
COPY poetry.lock pyproject.toml ./

# Install dependencies, creating the .venv directory
RUN poetry install --without dev --no-root

# Copy source code
COPY scheduler_service ./scheduler_service

# Build the package
RUN poetry build


# Stage 3: Runner - Create the final lightweight image
FROM python:3.14-alpine AS runner

# Set working directory for installation
WORKDIR /app

# Copy the built wheel from the builder stage
COPY --from=builder /app/dist/*.whl .

# Install dependencies and perform aggressive cleanup
# 1. Install build-base (contains gcc and strip)
# 2. Install python packages
# 3. Strip debug symbols from .so files (drastically reduces size of C-extensions)
# 4. Remove cached bytecode (__pycache__)
# 5. Remove build tools and wheel files
RUN apk add --no-cache --virtual .build-deps build-base \
    && pip install --no-cache-dir *.whl \
    && find /usr/local/lib/python3.14/site-packages -name "*.so" -exec strip --strip-all {} + \
    && find /usr/local/lib/python3.14/site-packages -name "__pycache__" -type d -exec rm -rf {} + \
    && apk del .build-deps \
    && rm -f *.whl

# Create a non-root user and its home directory
RUN addgroup -S appgroup && adduser -S -h /home/appuser -G appgroup appuser

# Switch to the non-root user
USER appuser

# Set the final working directory
WORKDIR /home/appuser/app

# Copy frontend build artifacts from frontend-builder
# We copy them to a 'static' directory inside the package or reachable location
# The plan mentioned copying to scheduler_service/static
# However, since we installed the package via wheel, we should probably copy to a well-known location 
# and tell the app where to find it. But wait, main.py is part of the installed package.
# A simpler way for a container is to map a folder in the container to serve.
# Let's copy to /home/appuser/app/static and configure main.py to look there.
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose the port
EXPOSE 8000

# Command to run the application
# PYTHONDONTWRITEBYTECODE=1 prevents python from writing .pyc files at runtime
ENV PYTHONDONTWRITEBYTECODE=1

# We need to inform the app where static files are if not in default package location
# But sticking to the plan: "Copy Frontend build artifacts ... to scheduler_service/static"
# Since we install as a package, putting it inside the package dir after install is tricky without editable install.
# Better to put it in a separate folder (like ./static) and have main.py look for it relative to CWD or ENV.
# I will proceed with copying to `./static` (which is /home/appuser/app/static) and update main.py accordingly.

CMD ["scheduler", "runserver", "--host", "0.0.0.0", "--port", "8000"]