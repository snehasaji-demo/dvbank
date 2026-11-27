FROM python:3.9-slim

RUN (sed -i 's#http://#https://#g' /etc/apt/sources.list.d/*.sources /etc/apt/sources.list 2>/dev/null || true) && apt-get update && apt-get upgrade -y --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]