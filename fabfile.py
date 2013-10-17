from fabric.api import lcd, local, cd, prefix, env
from contextlib import contextmanager as _contextmanager

env.directory = '/home/dax/pypo'
env.activate = '. /home/dax/pypo_env/bin/activate'

@_contextmanager
def virtualenv():
    with cd(env.directory):
        with prefix(env.activate):
            yield

def update_server():
    with virtualenv():
	    local('git pull')
            local('./manage.py migrate')
	    local('sudo service apache2 restart')


