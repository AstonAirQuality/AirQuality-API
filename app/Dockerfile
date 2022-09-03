FROM python:3.10.6-slim-buster
ENV PYTHONUNBUFFERED=1
# TODO remove env folder,env file, docker/docker-db and sql files, and docker-compose.yml
WORKDIR /app
COPY AirQuality-API.requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . /app
EXPOSE 8000