from django.core.management.base import BaseCommand
from wsgiref.simple_server import make_server
from wise.internal.health_check import health_check as hc
import json


def health_wsgi_app(environ, start_response):
    health = hc.check_all_with_titles()

    # Response setup
    status_code = "200 OK" if all(health.values()) else "503 Service Unavailable"
    response_body = json.dumps(health).encode("utf-8")

    headers = [
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(response_body))),
    ]

    start_response(status_code, headers)
    return [response_body]


class Command(BaseCommand):
    help = "Run a simple WSGI health check server"

    def add_arguments(self, parser):
        parser.add_argument(
            "host",
            nargs="?",
            default="127.0.0.1",
            help="Host interface to bind the health server to (default: 127.0.0.1)",
        )
        parser.add_argument(
            "port",
            nargs="?",
            type=int,
            default=8080,
            help="Port to run the health server on (default: 8080)",
        )

    def handle(self, *args, **options):
        host = options["host"]
        port = options["port"]

        self.stdout.write(
            self.style.SUCCESS(f"Starting health check server on port {port}...")
        )
        with make_server(host, port, health_wsgi_app) as httpd:
            self.stdout.write(
                self.style.SUCCESS("Health check server running. Press Ctrl+C to stop.")
            )
            httpd.serve_forever()
