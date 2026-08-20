FROM python:3.12-slim

WORKDIR /app

# Install dependencies as a separate layer so Docker cache reuses it
# when only source code changes (not requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium --with-deps

COPY . .

CMD ["python", "main.py"]
