"""
demo_api.py

API local de demostración para la presentación.

- UP cuando está corriendo
- DOWN cuando la apagas con Ctrl+C (sin traceback)
- RECOVERED cuando la vuelves a encender
"""

from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)  # UP
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Demo API is running")

    def log_message(self, format, *args):
        return  # evita spam en consola


def main():
    server = HTTPServer(("127.0.0.1", 8000), Handler)

    print("✅ Demo API UP corriendo en:")
    print("   http://127.0.0.1:8000")
    print("   (Ctrl+C para apagar y simular DOWN)\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        # salida limpia, sin traceback
        print("\n🛑 Demo API detenida (Ctrl+C).")
    finally:
        # libera el puerto correctamente
        server.server_close()


if __name__ == "__main__":
    main()
