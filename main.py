from dotenv import load_dotenv
load_dotenv()  # carga .env automáticamente

import sys
import threading

from core.logic import add_API_database
from core.runner import empezar_monitoreo


def help_msg():
    print(
        "Uso:\n"
        "  python main.py run\n"
        "  python main.py serve\n"
        "  python main.py both\n"
        "  python main.py add \"Nombre\" \"URL\"\n"
        "  python main.py add   (modo interactivo)\n\n"
        "Ejemplo:\n"
        "  python main.py add \"Cat Facts\" \"https://catfact.ninja/fact\"\n"
        "  python main.py both\n"
    )


def add_interactive():
    print("📝 Agregar API (modo interactivo)")
    name = input("Nombre de la API: ").strip()
    url = input("URL de la API (http/https): ").strip()

    try:
        add_API_database(name, url)
        print("✅ API agregada/ya existente.")
    except ValueError as e:
        print(f"❌ {e}")


def serve_api():
    import uvicorn
    uvicorn.run("core.api_server:app", host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        empezar_monitoreo()
        raise SystemExit(0)

    cmd = sys.argv[1].lower()

    if cmd == "run":
        empezar_monitoreo()
        raise SystemExit(0)

    if cmd == "serve":
        serve_api()
        raise SystemExit(0)

    if cmd == "both":
        t = threading.Thread(target=empezar_monitoreo, daemon=True)
        t.start()
        serve_api()
        raise SystemExit(0)

    if cmd == "add":
        # Interactivo
        if len(sys.argv) < 4:
            add_interactive()
            raise SystemExit(0)

        # No interactivo
        name = sys.argv[2].strip()
        url = sys.argv[3].strip()

        try:
            add_API_database(name, url)
            print("✅ API agregada/ya existente.")
        except ValueError as e:
            print(f"❌ {e}")
            raise SystemExit(1)

        raise SystemExit(0)

    help_msg()
    raise SystemExit(1)
