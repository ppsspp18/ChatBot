FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source is bind-mounted by docker-compose for live editing,
# this COPY just makes the image runnable standalone too.
COPY . .

EXPOSE 8501

# runOnSave + polling file watcher => hot reload works reliably
# even on bind-mounted volumes (same approach as your backend's
# WATCHFILES_FORCE_POLLING).
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.runOnSave=true", \
     "--server.fileWatcherType=poll"]
