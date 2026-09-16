# RentCheck Tanzania

A bilingual (English / Kiswahili) rental marketplace for the Tanzanian market. Owners and agents list properties, tenants apply to rent with a simple agreement-based flow, and landlords review applications, run a screening scorecard, and approve or reject tenants.

## Features

- **Property listings** with search, filters, pagination, and rich cards updated live from the database.
- **Role-based dashboards** for Admins, Owners/Agents, and Tenants.
- **Simplified rental application** — applicants only provide contact details, read the property's **Tenancy Rules**, and tick an agreement checkbox. No employment, income, reference, or document collection, and no per-listing custom questions.
  - The agreement is enforced **server-side**, not just on the form: submitting without accepting is rejected.
  - Pending duplicate applications are blocked; rejected applicants can re-apply; applying to your own listing is blocked.
- **Owner application pipeline** — view, approve, reject (with a decision note), and mark a property as rented (rented properties reject new applications and hide from browse).
- **Tenant screening scorecard** — owner fills a checklist, the app computes a 0–100 score and stores it with the application.
- **Engagement tools** — booking requests, viewing scheduling, enquiries with owner responses, favorites, reviews, and an in-site conversation thread with notifications.
- **Full English / Swahili internationalization** (`/sw/` prefix + EN/SH navbar toggle).

## Tech stack

- Python 3.12 · Django 5.2
- PostgreSQL (psycopg 3)
- Cloudinary for image storage (falls back to local media when unset)
- Whitenoise for static files · Gunicorn for serving
- Deployed on Render (`render.yaml`)

## Project structure

```
PEPE/            Django project (settings, root urls)
accounts/        Custom user with TENANT / OWNER_AGENT / ADMIN roles, auth flow
properties/      Property models, browse/detail, owner-managed listings
engagement/      Applications, approvals, screening, bookings, viewings,
                 enquiries, favorites, reviews, reports, notifications
core/            Home, dashboards, decorators, shared views
templates/       Project-wide templates (base + language switch partial)
locale/sw/       Swahili translation catalog (PO + compiled MO)
```

## Local setup

1. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv venv
   # Windows:  venv\Scripts\activate
   # macOS/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy the environment template and fill in real values (at minimum a new `SECRET_KEY`):

   ```bash
   cp .env.example .env
   ```

3. Create a local PostgreSQL database matching the `DB_*` values in `.env` (or set `DATABASE_URL` to point anywhere).

4. Run migrations and start the dev server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

   The app runs at <http://127.0.0.1:8000/>.

## Translating (i18n)

Languages are `en` and `sw`. Non-default-language URLs are prefixed (e.g. `/sw/properties/`); the default language keeps clean URLs. The toggle in the navbar posts to `set_language` and redirects to the same page in the new language.

After changing any user-visible strings from templates/views/forms/models:

```bash
python manage.py makemessages -l sw --no-wrap --ignore "*venv*" --ignore "static/*" --ignore "media/*"
# edit locale/sw/LC_MESSAGES/django.po, then:
python manage.py compilemessages
```

Commit both the `.po` and the compiled `.mo`. Keep `%(...)s` placeholders and `%%` intact in translations. User-created content (titles, descriptions, tenancy rules) is never machine-translated — only the UI.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

`--check --dry-run` intentionally reports drift for the pre-existing `accounts/0003_alter_user_managers` migration — do not create or commit it.

## Deployment (Render)

- `render.yaml` provisions the `rentcheck-tanzania` web service (free plan, `gunicorn PEPE.wsgi:application`).
- `build.sh` runs on build: installs requirements, collects static files, runs `manage.py migrate`, and bootstraps/updates a superuser.
- Set `SECRET_KEY`, `DATABASE_URL`, `CLOUDINARY_URL`, and `ALLOWED_HOSTS` as service env vars (see `.env.example`).
- Deploys are **manual**: push to `main`, then in the Render dashboard choose **Manual Deploy → Deploy latest commit**.
- Cannot migrate on the free plan during initial deploy quiescence; if a migrate is retried by Render's restart it is safe (migrations are idempotent).