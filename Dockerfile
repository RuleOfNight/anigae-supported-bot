FROM python:3.12-slim

WORKDIR /app

# Install dependencies as a separate layer so Docker cache reuses it
# when only source code changes (not requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN playwright install chromium --with-deps

CMD ["python", "main.py"]
