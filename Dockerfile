FROM python:3.11-alpine3.17

# Add necessary package for cryptography
RUN apk update && apk add python3-dev \
    gcc \
    libc-dev \
    libffi-dev

WORKDIR /code
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/code

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

# Copy code
COPY locker_api/ code/

EXPOSE 5000

CMD ["python3", "code/main.py"]
