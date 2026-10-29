# Campus to Career — Full-stack version

This project includes a real Python Flask backend and database-backed features.

## Working features
- Student and company account registration
- Password hashing
- Login and logout
- Company job/internship posting
- Job listings and search
- Students applying for jobs
- Student dashboard showing their applications and statuses
- Company dashboard showing applications and allowing status updates
- SQLite by default for local testing; PostgreSQL when `DATABASE_URL` is set

## Run on Windows with VS Code

1. Install Python 3.11 or newer.
2. Extract the ZIP and open this folder in VS Code.
3. Open Terminal → New Terminal.
4. Run:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

5. Open http://127.0.0.1:5000 in your browser.

If `py` does not work, try `python` instead.

## Deploy on Render
1. Upload all project files (including `app.py`, `templates`, `static`, `requirements.txt`, and `render.yaml`) to a GitHub repository.
2. In Render, choose New → Blueprint and connect the repository. Render reads `render.yaml` to create the web service and PostgreSQL database.
3. Wait for deployment and open the Render URL.

If Render does not offer a free PostgreSQL plan for your account/region, select an available PostgreSQL plan and ensure `DATABASE_URL` is set on the web service.

## Important
- Use a strong, private `SECRET_KEY` in production; Render's blueprint generates one automatically.
- This is a college project starter, not a fully audited production recruitment platform. Add email verification, password reset, rate limiting, CSRF protection, privacy/consent text, and moderation before public commercial use.
- The sample AI career buddy from the earlier static demo is not a real AI integration in this backend version.
