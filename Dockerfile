# This file is only needed if you need to create your own Plex Light container image.
# A pre-built image is available in Docker.io: https://hub.docker.com/repository/docker/randyoyarzabal/plex_light
# via the command: $> docker pull randyoyarzabal/plex_light:latest
#
# HOW TO USE THIS FILE
# 
# While in the same directory as this file...
#
# Build Container:
# $> docker build -t randyoyarzabal/plex_light .
#
# Using the Container:
#
# Run container in background once:
#   - $> sudo docker run --rm -d -t \
#           -v <config dir path>:/plex_light/config \
#           -e PL_CONFIG_FILE='/plex_light/config/.env'
#           -p 5000:5000 \
#           --name=plex_light \
#           --restart=unless-stopped
#           randyoyarzabal/plex_light
# 
# This is a multi-stage build file that significantly minimizes the container image size.

# Stage 1
FROM python:3.9-slim AS compile-image

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel;

# Ignore versions
RUN cat requirements.txt | cut -d'=' -f 1 | xargs pip install --upgrade;

# Adhere to versions defined.
#RUN pip install -r requirements.txt

# Stage 2
FROM python:3.9-slim AS build-image
ENV PL_PATH="/plex_light"
ENV PATH="/opt/venv/bin:$PL_PATH:$PATH"

WORKDIR $PL_PATH

COPY --from=compile-image /opt/venv /opt/venv
COPY . $PL_PATH

CMD ["plex_light.py"]
