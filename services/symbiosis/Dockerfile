FROM python:3.11
WORKDIR /atelier

COPY services/symbiosis/requirements.txt /atelier/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /atelier/requirements.txt

COPY packages/symbiosis /atelier/symbiosis
COPY packages/communal /atelier/communal

CMD ["gunicorn", "--bind", "0.0.0.0:33333", "-k", "uvicorn_worker.UvicornWorker", "-w", "1", "symbiosis.entrypoint:app"]
