FROM ubuntu:22.04 as dev-env

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    && apt clean

# Get basic Python Dependencies
RUN pip install --upgrade virtualenv

# Create and prioritize the virtual environment
ENV VIRTUAL_ENV=/app/schema/venv
RUN virtualenv -p python3.11 $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY ./requirements.txt /app/schema/
RUN pip install -r /app/schema/requirements.txt
