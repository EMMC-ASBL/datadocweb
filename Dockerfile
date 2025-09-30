FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && apt-get clean

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["bash", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
