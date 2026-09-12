# new_try

A Flask-based web application with dashboard views, Excel processing and download utilities, database models, email configuration, and Microsoft authentication support.

## Project structure

- `run.py` — application entry point
- `flaskr/` — Flask application package
  - `templates/` — base, index, and dashboard pages
  - `static/` — frontend assets
  - `process_excel.py` and `excel_download.py` — Excel workflow utilities
  - `models.py` and `final_db.py` — data-model and database utilities
  - `msal_auth.py`, `auth_config.py`, and `mail_config.py` — authentication and email configuration
- `requirements.txt` — Python dependencies
- `Procfile` — process definition for deployment

## Run locally

```bash
pip install -r requirements.txt
python run.py
```

Configure the required environment variables and service credentials before starting the application.
