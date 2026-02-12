import logging
import os
import sys
from flask import Flask

from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource


SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "flask-default")
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector:4317")
INSECURE = os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true"

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

resource = Resource.create({
    "service.name": SERVICE_NAME
})

logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)

otlp_exporter = OTLPLogExporter(
    endpoint=OTLP_ENDPOINT,
    insecure=INSECURE
)

logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(otlp_exporter)
)

logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(ConsoleLogExporter())
)

otel_handler = LoggingHandler(
    level=logging.INFO,
    logger_provider=logger_provider
)

stdout_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.INFO,
    handlers=[otel_handler, stdout_handler],
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("flask-app")

app = Flask(__name__)

@app.route("/")
def home():
    logger.info(
        "Home endpoint hit",
        extra={
            "http.method": "GET",
            "http.path": "/" 
        }
    )
    return "Hello from Flask + OTEL + Docker"

@app.route("/error")
def error():
    logger.error(
        "Error endpoint hit",
        extra={
            "http.method": "GET",
            "http.path": "/error",
            "error.type": "CustomError"
        }
    )
    return "Error logged", 500

@app.route("/container")
def container():
    logger.info(
        "Container endpoint hit",
        extra={
            "http.method": "GET",
            "http.path": "/container"
        }
    )
    return "Hello from container"

if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT)
