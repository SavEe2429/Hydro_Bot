# Hydro_Bot

A compact project combining an ESP32 controller, a Python backend, a Vue frontend, and an object-detection model for automating hydroponics tasks.

## Overview

- **Backend/**: Python services for device communication and control.
- **Frontend/**: Vue app for user interface and control panel.
- **ESP32/**: PlatformIO firmware for the microcontroller.
- **Model/**: YOLO-based detection scripts and weights.

## Quick Start

Prerequisites:

- Python 3.8+
- pip
- Node.js + npm
- PlatformIO (for ESP32 builds)

Backend (local dev):

1. Create a virtualenv and install requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the main backend app:

```powershell
python Backend\app.py
```

Frontend (dev):

```powershell
cd Frontend
npm install
npm run dev
```

ESP32 (build & upload):

1. Open the `ESP32` folder in PlatformIO or use CLI:

```powershell
cd ESP32
pio run -e <env> -t upload
```

Model (inference):

```powershell
python Model\detect.py --weights Model\best.pt --source <image_or_video>
```

## Running End-to-End

1. Flash ESP32 firmware and connect device to host.
2. Start the Backend services (`Backend\app.py`).
3. Launch the Frontend dev server and open the UI.
4. Use the UI to send commands; backend forwards to device via serial/listener.

## Repository Structure

- `Backend/` — Flask or FastAPI app and listener utilities.
- `Frontend/` — Vue 3 app built with Vite.
- `ESP32/` — PlatformIO firmware sources.
- `Model/` — Detection scripts and trained weights.

## Dependencies

This project uses several language-specific libraries and tools across components.

- Python (Backend & Model):
	- Flask
	- requests
	- gunicorn
	- flask-cors
	- pyserial
	- numpy
	- opencv-python
	- ultralytics (YOLO model runtime)

	Install Python deps:

	```powershell
	pip install -r requirements.txt
	pip install ultralytics
	```

- Frontend (Node):
	- vue
	- vue-router
	- axios
	- vite (dev/build)
	- eslint, prettier (dev tooling)

	Install Frontend deps:

	```powershell
	cd Frontend
	npm install
	```

- ESP32 / PlatformIO:
	- PlatformIO Core (CLI or VS Code extension)
	- Platform: `espressif32`
	- Framework: `arduino`

	Build/upload with PlatformIO in the `ESP32` folder.

## Troubleshooting

- If the backend cannot reach the device, check serial port permissions and `Backend/local_listener.py` configuration.
## Troubleshooting

- If the backend cannot reach the device, check serial port permissions and `Backend/local_listener.py` configuration.
- For model issues, ensure `Model/best.pt` exists and `opencv-python` is installed.

## Contributing

Open an issue or PR with a clear description and reproduction steps.

---

If you'd like, I can also:

- add more detailed run examples for each component,
- create README sections per OS, or
- add CI/dev scripts for building the ESP32 and running the frontend/backend.
