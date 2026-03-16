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
    shadow \
    && rm -rf /var/cache/apk/*

# Add jenkins user to docker group (using host socket's GID)
RUN set -ex; \
    DOCKER_GID=$(stat -c %g /var/run/docker.sock 2>/dev/null || echo 999); \
    if getent group $DOCKER_GID > /dev/null 2>&1; then \
        EXISTING_GROUP=$(getent group $DOCKER_GID | cut -d: -f1); \
        adduser jenkins $EXISTING_GROUP; \
    else \
        addgroup -g $DOCKER_GID docker; \
        adduser jenkins docker; \
    fi

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
ENV PATH="/var/jenkins_home/.local/bin:${PATH}"