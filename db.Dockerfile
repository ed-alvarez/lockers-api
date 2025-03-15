FROM postgres:15.1-alpine3.16

ENV POSTGRES_USER=koloni
ENV POSTGRES_PASSWORD=4B9eYLxnld5I
ENV POSTGRES_DB=docker

COPY init.sql /docker-entrypoint-initdb.d/

EXPOSE 5432

CMD ["postgres"]
