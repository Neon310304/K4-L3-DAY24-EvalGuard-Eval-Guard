FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1 TOKENIZERS_PARALLELISM=false
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY requirements/ /tmp/requirements/
RUN uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system -r /tmp/requirements/requirements.txt -c /tmp/requirements/constraints-core.txt
ARG SPACY_MODEL_URL=https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl#sha256=293e9547a655b25499198ab15a525b05b9407a75f10255e405e8c3854329ab63
RUN uv pip install --system --no-deps "$SPACY_MODEL_URL"
RUN uv pip check --system && python -c "import ragas, nemoguardrails, presidio_analyzer, spacy, sentence_transformers; spacy.load('en_core_web_lg'); print('Full runtime imports OK')"
CMD ["python", "scripts/check_lab.py"]
