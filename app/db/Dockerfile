FROM postgres:14.1

RUN apt-get update \
    && apt-get install wget -y \
    && apt-get install postgresql-14-postgis-3 -y \
    && apt-get install postgis -y

COPY ./db.sql /docker-entrypoint-initdb.d/