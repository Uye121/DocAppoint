FROM jenkins/jenkins:lts-alpine-jdk21

USER root

# Install tools using apk (Alpine package manager)
RUN apk update && apk add --no-cache \
    python3 \
    py3-pip \
    nodejs \
    npm \
    make \
    curl \
    docker-cli \
    && rm -rf /var/cache/apk/*

# Install Docker Compose plugin
RUN mkdir -p /usr/local/lib/docker/cli-plugins && \
    curl -SL https://github.com/docker/compose/releases/download/v2.39.2/docker-compose-linux-x86_64 \
    -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Create cache directories with proper permissions
RUN mkdir -p /cache/npm /cache/poetry && \
    chown -R jenkins:jenkins /cache

USER jenkins

RUN curl -sSL https://install.python-poetry.org | python3 -

# Add poetry to PATH
ENV PATH="/home/jenkins/.local/bin:${PATH}"