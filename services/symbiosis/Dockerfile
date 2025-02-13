FROM python:3.11
WORKDIR /atelier

COPY ./requirements.txt /atelier/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /atelier/requirements.txt

COPY packages/symbiosis /atelier/symbiosis

CMD ["fastapi", "run", "symbiosis/entrypoint.py", "--port", "33333", "--workers", "1"]
