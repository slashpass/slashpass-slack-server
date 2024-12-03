FROM python:3.12-alpine

# Set environment variables to avoid Python bytecode and Poetry virtualenvs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false

# Install dependencies
RUN apk update && apk add --no-cache \
    g++ \
    gcc \
    postgresql-dev \
    musl-dev \
    libffi-dev \
    curl \
    bash

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies using Poetry
RUN poetry install --no-root

# Expose the application port
EXPOSE 8000

# Set the default command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi"]
