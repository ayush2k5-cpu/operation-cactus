FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
COPY backend ./backend
COPY capture ./capture
COPY contracts ./contracts
COPY covertrace ./covertrace
COPY flowsight ./flowsight
COPY mimicnet ./mimicnet

EXPOSE 8000
CMD ["python", "-m", "backend.gkmkb", "serve"]
