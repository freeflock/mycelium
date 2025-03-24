FROM python:3.11
WORKDIR /atelier

COPY services/spread/requirements.txt /atelier/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /atelier/requirements.txt

COPY packages/spread /atelier/spread
COPY packages/communal /atelier/communal

CMD ["python3", "-m", "spread.entrypoint"]
