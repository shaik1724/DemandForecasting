# How to Run: Product Demand Forecasting

Follow these steps to set up and run the Demand Forecasting system.

## 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

## 2. Install Dependencies
Open your terminal (PowerShell or CMD) in the project root folder and run:
```powershell
pip install -r requirements.txt
```

## 3. Run the Application
To start the backend server and the frontend dashboard, use the following command:
```powershell
python -m backend.main
```

> [!IMPORTANT]
> **Why use `-m`?** 
> This runs the backend as a module, which ensures all internal imports (like `from backend.models ...`) work correctly without "Module Not Found" errors.

## 4. Open the Dashboard
Once the server starts (you will see `Uvicorn running on http://0.0.0.0:8000`), open your browser and go to:
**[http://localhost:8000/app](http://localhost:8000/app)**

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'backend'"
Ensure you are running the command from the **root directory** (the folder containing `requirements.txt`) and using the `python -m backend.main` syntax.

### Port 8000 already in use
If the server fails to start because port 8000 is busy, you can change the port in `backend/main.py` at the bottom of the file or run:
```powershell
uvicorn backend.main:app --port 8080
```
Then visit `http://localhost:8080/app`.
