# APIs Automated Monitor

Sistema de monitoreo automatizado de APIs que combina **Python (FastAPI)** y **Node.js** para levantar un backend, un monitor, un dashboard web y servicios opcionales como un bot de Telegram.

**APIs Automated Monitor** permite:

* Monitorear APIs de forma automática
* Levantar múltiples servicios con un solo comando
* Visualizar resultados desde un dashboard web
* Enviar notificaciones (Telegram)
* Probar APIs demo para desarrollo

**Para informacion extra de proceso**
https://www.notion.so/Monitoreo-automatizado-de-APIs-2f949a03b2df808eac9de2273015298a?source=copy_link

---

## Tecnologías usadas

### Backend

* **Python 3.8+**
* **FastAPI**
* **Uvicorn**

### Frontend

* **Node.js (LTS)**
* **npm**
* Dashboard web (Vite / stack frontend)

### Otros

* Bot de Telegram (opcional)
* APIs demo
* PowerShell para automatización

---

## Estructura del proyecto

```
APIs-automated-monitor/
│
├── core/                  # Backend FastAPI
├── dashboard/             # Frontend (Node.js)
├── telegram/              # Bot de Telegram
│   └── telegram_bot.py
├── demos/                 # APIs demo
│   └── demo_api.py
├── venv/                  # Entorno virtual Python
├── docs/                  # Docuemntacion y documentos
│   └── README.md
├── run-all.ps1            # Script principal de arranque
├── requirements.txt       # Dependencias Python
└──.env                   # Variables de entorno

```

---

## Requisitos previos

Asegurate de tener instalado:

* **Python 3.8 o superior**
* **Node.js (LTS)** → incluye `npm`
* **PowerShell** (Windows)

Verificá:

```powershell
python --version
node -v
npm -v
```

---

## Configuración

### Clonar el repositorio

```bash
git clone https://github.com/SadCloud03/APIs-automated-monitor.git
cd APIs-automated-monitor
```

### Crear archivo `.env`

En la raíz del proyecto:

```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
```

> El bot de Telegram es opcional.

---

## Levantar todo el proyecto

Desde la raíz del proyecto:

```powershell
.\run-all.ps1
```

Este script:

1. Verifica que **Python y npm** estén en el PATH
2. Crea / usa el entorno virtual (`venv`)
3. Instala dependencias de Python
4. Instala dependencias del frontend (`npm install`)
5. Levanta todos los servicios en ventanas separadas

---

## Servicios levantados

| Servicio           | URL / Info                                     |
| ------------------ | ---------------------------------------------- |
| Backend API        | [http://127.0.0.1:8001](http://127.0.0.1:8001) |
| Frontend Dashboard | [http://localhost:5173](http://localhost:5173) |
| Demo API           | [http://127.0.0.1:8000](http://127.0.0.1:8000) |
| Telegram Bot       | Enviar `/start` al bot                         |

---

## Ejecución manual (opcional)

### Backend API

```bash
python -m uvicorn core.api_server:app --reload
```

### Frontend

```bash
cd dashboard
npm install
npm run dev
```

---

## Problemas comunes

### npm no encontrado

Si PowerShell encuentra `node` pero VS Code no:

```bash
code .  # abrir VS Code desde PowerShell
```

O reiniciá VS Code para que herede el PATH.

---

