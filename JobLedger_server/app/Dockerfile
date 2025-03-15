FROM python:3.10-slim

WORKDIR /app

RUN python -m venv /venv

RUN /venv/bin/pip install --upgrade pip

COPY requirements.txt /app/
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . /app/

# Set environment variable for Flask
ENV FLASK_APP=app

EXPOSE 8080

CMD ["/bin/bash", "-c", "/venv/bin/waitress-serve --host=0.0.0.0 --port=8080 app:app"]