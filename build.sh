#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py createsuperuser --no-input || true
python manage.py shell -c "from accounts.models import User; User.objects.filter(is_superuser=True).update(role='ADMIN')" || true