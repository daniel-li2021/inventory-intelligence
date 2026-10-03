# Base manifest is pinned; the built application image still needs release acceptance.
ARG PYTHON_IMAGE=python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
FROM ${PYTHON_IMAGE} AS build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /build
COPY pyproject.toml README.md ./
COPY deploy/lab/requirements.txt ./requirements.txt
COPY src ./src
COPY sql/checks.sql sql/views.sql ./sql/
RUN python -m pip install --no-cache-dir pip==25.2 setuptools==80.9.0 wheel==0.45.1 \
    && python -m pip wheel --no-cache-dir --no-build-isolation --wheel-dir /wheels --constraint requirements.txt '.[lab]'

FROM ${PYTHON_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY --from=build /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links /wheels inventory-intelligence[lab] \
    && rm -rf /wheels
USER 10001:10001
WORKDIR /tmp
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import json,urllib.request; d=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/evidence',timeout=3)); assert d['synthetic'] is True and d['business_data']=='synthetic only'"
CMD ["python", "-m", "uvicorn", "inventory_intelligence.lab_hosted:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "16", "--backlog", "32", "--timeout-keep-alive", "5", "--no-access-log", "--no-proxy-headers"]
