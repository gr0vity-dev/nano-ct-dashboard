FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app app

#CMD ["gunicorn", "-w", "4", "-k", "quart.gunicorn.QuartWorker", "app:app"]
CMD ["hypercorn", "-w", "4", "-b", "0.0.0.0:5000", "app.app:app"]


