FROM python:3.11
WORKDIR /atelier

COPY ./requirements.txt /atelier/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /atelier/requirements.txt

COPY packages/mycelium /atelier/mycelium

CMD ["fastapi", "run", "mycelium/symbiosis/entrypoint.py", "--port", "33333", "--workers", "1"]
