FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

RUN useradd --uid 10001 --create-home app \
    && mkdir -p /app/instance \
    && chown app:app /app/instance

USER app

EXPOSE 5000

CMD ["sh", "-c", "python -m src.db.init_db && exec flask --app src.app run --host=0.0.0.0 --port=5000"]
