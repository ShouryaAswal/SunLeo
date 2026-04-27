FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and Firebase service account
COPY ./app ./app
COPY ./sunleo-d0820-firebase-adminsdk-fbsvc-3f8a4da36d.json ./sunleo-d0820-firebase-adminsdk-fbsvc-3f8a4da36d.json

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
