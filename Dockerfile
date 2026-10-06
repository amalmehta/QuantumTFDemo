# Quantum TF Demo — reproducible runtime for TensorFlow Quantum 0.7.6 (Linux x86_64 wheels).
FROM python:3.11-slim
ENV TF_USE_LEGACY_KERAS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TF_CPP_MIN_LOG_LEVEL=2 MPLBACKEND=Agg
WORKDIR /work
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt
CMD ["python", "-m", "quantumtf_demo.run_all"]
