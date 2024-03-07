# Start from a Jupyter Docker Stacks version - ARM compatible
FROM jupyter/scipy-notebook:latest

# Needed for poetry package management: no venv, latest poetry, GRANT_SUDO don't work :(
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=1.8.2 \
    GRANT_SUDO=yes

# The docker stacks make sudo very difficult, so we [just be root™]
USER root
RUN sudo apt update && \
    sudo apt upgrade -y && \
    sudo apt install curl graphviz graphviz-dev -y && \
    rm -rf /var/lib/apt/lists/*

# Go back to jovyan user so we don't have permission problems
USER ${NB_USER}

# Install pipx so we can install poetry system wide
RUN python3 -m pip install --no-cache-dir --user pipx && \
    python3 -m pipx ensurepath

# Now install poetry to install our dependencies
ENV PATH "/home/jovyan/.local/bin:$PATH"
RUN pipx install poetry==${POETRY_VERSION}

# Copy our poetry configuration files as jovyan user
COPY --chown=${NB_UID}:${NB_GID} pyproject.toml "/home/${NB_USER}/work/"
COPY --chown=${NB_UID}:${NB_GID} poetry.lock    "/home/${NB_USER}/work/"

EXPOSE 8888

# Install our package requirements via poetry. No venv. Squash max-workers error.
WORKDIR "/home/${NB_USER}/work"
RUN poetry config virtualenvs.create false && \
    poetry config installer.max-workers 10 && \
    poetry install --no-interaction --no-ansi --no-root -vvv && \
    poetry cache clear pypi --all -n
