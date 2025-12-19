FROM python:3.11-slim

# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1 \
#Prevents Python from buffering stdout and stderr
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy project
COPY . .

RUN mkdir -p /app/media/speciality /app/media/healthcare_providers

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]