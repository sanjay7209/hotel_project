# Hotel Project

A simple FastAPI-based hotel management app.

## Setup (Windows, PowerShell)

1. Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

2. Upgrade pip and install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Create `.env` from `.env.example` and fill in secrets:

```powershell
copy .env.example .env
# then edit .env in your editor and replace placeholders
```

4. (Optional) Seed rooms data:

```powershell
python master_data.py
```

5. Run the FastAPI app:

```powershell
uvicorn main:app --reload
```

6. Open the notebook (optional):

Start Jupyter Lab or Notebook and open `langchain.ipynb`.

```powershell
python -m jupyter lab
```

## Notes
- Do NOT commit real secrets. `.env` is in `.gitignore`.
- The project expects a MySQL database configured in `DATABASE_URL`.

