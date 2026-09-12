# Portal Release Tracker — Indus International

Flask web application for tracking FG (Finished Goods) portal releases at Indus International FZC. Allows the operations team to log, view, and manage product release entries against open Purchase Orders, with Microsoft 365 SSO login, PostgreSQL persistence, and automated email notifications.

## What It Does

- **Microsoft 365 SSO** — login via MSAL (Azure AD OAuth2), no separate password needed
- **Release Logging** — operators record FG releases: Indus Part, Customer, Pallet count, Quantity, PO reference
- **PO Allocation** — release quantities are automatically allocated against open PO lines (grouped by `indus_part`), with zero-quantity and zero-pallet rows filtered out
- **Releases Tab** — view all logged releases with filtering; rows with zero pallets/quantity are excluded from display
- **Excel Export** — download the full releases log as a formatted `.xlsx` file
- **Email Notifications** — sends release confirmation emails via Microsoft Graph API (Mail)
- **PostgreSQL backend** — all data persisted in a Heroku Postgres database

## Project Structure

```
new_try/
├── flaskr/
│   ├── __init__.py        # App factory, blueprint registration
│   ├── views.py           # All route handlers (main, releases, exports)
│   ├── models.py          # SQLAlchemy models (Release, POLine, etc.)
│   ├── final_db.py        # Database init and query helpers
│   ├── process_excel.py   # Inbound PO Excel processing logic
│   ├── excel_download.py  # Outbound Excel export builder
│   ├── msal_auth.py       # Microsoft 365 MSAL auth flow
│   ├── auth_config.py     # Azure AD app registration config
│   ├── mail_config.py     # Graph API mail send helpers
│   ├── static/            # CSS, JS assets
│   └── templates/         # Jinja2 HTML templates
├── run.py               # App entry point
├── Procfile             # Heroku process definition
├── requirements.txt     # Python dependencies
└── .python-version      # Python 3.11
```

## Tech Stack

- **Python 3.11 / Flask**
- **PostgreSQL** (Heroku Postgres)
- **MSAL** — Microsoft 365 / Azure AD authentication
- **Microsoft Graph API** — email sending
- **SQLAlchemy** — ORM
- **openpyxl / pandas** — Excel processing and export
- **Heroku** — deployment

## Setup (Local)

```bash
pip install -r requirements.txt
```

Set environment variables:

```
DATABASE_URL=postgresql://...
CLIENT_ID=...
CLIENT_SECRET=...
TENANT_ID=...
SECRET_KEY=...
```

Run:
```bash
python run.py
```

## Notes

- This is the **current active development repository** for the Portal Release Tracker
- Supersedes [`indus-inventory-deprecated`](https://github.com/ppc8040/indus-inventory-deprecated) and [`try1`](https://github.com/ppc8040/try1)
- Recent fix (April 2026): grouped `release_qty` by `indus_part` before PO allocation, and filtered zero-pallet/zero-quantity rows from the Releases tab

---
*Indus International FZC — Internal Tool*
