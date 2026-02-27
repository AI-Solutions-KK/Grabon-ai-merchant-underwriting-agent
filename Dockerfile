FROM python:3.11-slim

# Create non-root user matching HF Spaces UID
RUN useradd -m -u 1000 user

WORKDIR /code

# Ensure /code is owned by user 1000 so SQLite and any writes succeed
RUN chown user:user /code

# Copy and install deps as root first (faster layer caching)
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project and hand ownership to user 1000
COPY --chown=user . /code

# Switch to non-root user (required by HF Spaces)
USER user

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
