from os import path
from fabric.api import run, local, env
from fabric.contrib.files import exists

SITES_FOLDER = '/home/dax/sites'

REPO_URL = 'https://github.com/audax/pypo.git'

def deploy():
    _create_directory_structure_if_necessary(env.host)
    source_folder = path.join(SITES_FOLDER, env.host, 'source')
    _get_latest_source(source_folder)
    _update_virtualenv(source_folder)
    _update_static_files(source_folder)
    _update_database(source_folder)

def _create_directory_structure_if_necessary(site_name):
    base_folder = path.join(SITES_FOLDER, site_name)
    run('mkdir -p %s' % (base_folder)) #12
    for subfolder in ('database', 'static', 'virtualenv', 'source'):
        run('mkdir -p %s/%s' % (base_folder, subfolder))

def _update_virtualenv(source_folder):
    virtualenv_folder = path.join(source_folder, '../virtualenv')
    if not exists(path.join(virtualenv_folder, 'bin', 'pip')):
        run('virtualenv --python=python3.3 %s' % (virtualenv_folder,))
    run('%s/bin/pip install -r %s/requirements.txt' % (
        virtualenv_folder, source_folder
        ))


def _update_static_files(source_folder):
    run('cd %s && bower install' % source_folder)
    run('cd %s && lessc readme/static/less/readme.less readme/static/css/readme.css' % source_folder)
    run('cd %s && ../virtualenv/bin/python3 manage.py collectstatic --noinput -i test' % source_folder)


def _update_database(source_folder):
    run('cd %s && ../virtualenv/bin/python3 manage.py syncdb --noinput' % (
        source_folder,
        ))
    run('cd %s && ../virtualenv/bin/python3 manage.py migrate --noinput' % (
        source_folder,
        ))
    run('cd %s && ../virtualenv/bin/python3 manage.py update_index' % (
        source_folder,
        ))

def _get_latest_source(source_folder):
    if exists(path.join(source_folder, '.git')):
        run('cd %s && git fetch' % (source_folder,))
    else:
        run('git clone %s %s' % (REPO_URL, source_folder))
    current_commit = local("git log -n 1 --format=%H", capture=True)
    run('cd %s && git reset --hard %s' % (source_folder, current_commit))

def reload_wsgi():
    run("sudo service {}.gunicorn restart".format(env.host))
