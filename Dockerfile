FROM python:3.10
WORKDIR /app
RUN pip install --no-cache-dir poetry
COPY . .
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root
EXPOSE 8500 8501
CMD ["sh", "-c", "python relay.py & streamlit run main.py --logger.level=info --server.port 8501 --server.address 0.0.0.0"]
