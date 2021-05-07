ARG PYTHON_VERSION=3.7.10

FROM python:${PYTHON_VERSION}-slim as build-requirements

ARG SKIP_TEST

RUN \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

RUN echo "Installing Poetry" && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py \
    | python - --preview

WORKDIR /app
COPY pyproject.toml poetry.lock /app/

RUN \
    export PATH="$HOME/.local/bin:$PATH" ; \
    echo "Generate requirements.txt with Poetry" && \
    EXPORT_PARAMETERS="--without-hashes --with-credentials" && \
    poetry export ${EXPORT_PARAMETERS} -o ./requirements.txt && \
    if [ -z "$SKIP_TEST" ]; then cp requirements.txt r.txt && \
    echo "Also generate requirements-dev.txt for testing" && \
    EXPORT_PARAMETERS="$EXPORT_PARAMETERS --dev" && \
    poetry export ${EXPORT_PARAMETERS} -o ./r-dev.txt && \
    grep -Fvf r.txt r-dev.txt > requirements-dev.txt && \
    grep -Ff r.txt r-dev.txt > requirements.txt ; fi


FROM python:${PYTHON_VERSION}-slim

ARG SKIP_TEST

ENV PROJECT_DIR=/app
WORKDIR /app

COPY --from=build-requirements /app/requirements*.txt /app/
RUN \
    pip install --force-reinstall --ignore-installed --no-cache-dir \
    --use-feature=in-tree-build -r requirements.txt

COPY . /app
RUN \
    pip install --no-cache-dir \
    --use-feature=in-tree-build -r requirements.txt .

RUN \
    if [ -z "$SKIP_TEST" ]; then \
    pip install --force-reinstall --ignore-installed --no-cache-dir \
    --use-feature=in-tree-build -r requirements-dev.txt && \
    pylint --rcfile=pyproject.toml **/*.py ; \
    mypy --config-file=pyproject.toml -p bot --exclude 'utils/.*\\.py' && \
    pytest --cov=bot tests/ ; \
    pip uninstall -yr requirements-dev.txt ; else echo "Skip testing" ; fi

RUN rm -rf /app/bot
