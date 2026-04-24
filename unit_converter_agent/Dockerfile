FROM python:3.11-slim
WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser
USER appuser
ENV PATH="/home/appuser/.local/bin:$PATH"

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ADK api_server expects agents at /app/agents/<agent_name>/
COPY --chown=appuser:appuser . /app/agents/unit_converter_agent/

ENV PYTHONPATH="/app"
EXPOSE 8080

CMD ["adk", "api_server", "--port=8080", "--host=0.0.0.0", "--a2a", "/app/agents"]
