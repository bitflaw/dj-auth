FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY auth_pkg/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY auth_pkg/ .
EXPOSE 8000

# necessary to run migrations
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# only for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
