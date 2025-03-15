#!/bin/bash

# Run pg_dump command inside docker container
docker exec koloni-db pg_dump -U koloni -d docker > init.sql
