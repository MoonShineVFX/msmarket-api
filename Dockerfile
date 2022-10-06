FROM python:3.9-slim

ENV PYTHONUNBUFFERED TRUE
ENV PORT 80

WORKDIR /app

RUN pip install gunicorn
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 mysite.wsgi:application
