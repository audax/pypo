pip install -r requirements.txt --use-mirrors
psql -c 'create database pypo;' -U postgres
echo "DATABASES={'default':{'ENGINE':'django.db.backends.postgresql_psycopg2','NAME':'pypo','USER':'postgres','HOST':'127.0.0.1','PORT':5432}}" >> pypo/settings_local.py
sudo start xvfb
./manage.py test
