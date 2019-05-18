
from fabric.api import cd, env, lcd, put, prompt, local, sudo
from fabric.contrib.files import exists
import fabric.main


##############
### config ###
##############

git_repo_url = "https://github.com/codybaraks/FastDataGigs.git"
local_config_dir = './config'

remote_app_dir = '/home/www'
remote_git_dir = '/home/git'
remote_flask_dir = remote_app_dir + '/flask_project'
remote_nginx_dir = '/etc/nginx/sites-enabled'
remote_supervisor_dir = '/etc/supervisor/conf.d'

env.hosts = ['51.254.210.77']  # replace with IP address or hostname
env.user = 'root'
env.password = 'command.1'


def install_db():
    sudo('apt install mariadb-server mariadb-client')
    sudo('mysql_secure_installation')
    sudo('systemctl restart mariadb.service')
    sudo('apt install nginx')
    sudo('systemctl restart nginx.service')
    sudo('apt-get install php-fpm php-cgi php-common php-pear php-mbstring')
    sudo('apt-get install phpmyadmin php-gettext')
    sudo('ln -s /usr/share/phpmyadmin /var/www/html')
    sudo('mysql -u root')
    sudo('use mysql;')
    sudo("update user set plugin='' where User='root';")
    sudo('flush privileges;')
    sudo('exit')
    sudo('sudo systemctl restart mariadb.service')
    sudo('')
    sudo('')

def install_requirements():
    """ Install required packages. """
    sudo('apt-get update')
    sudo('apt-get install -y python')
    sudo('apt-get install -y python-pip')
    sudo('apt-get install -y python-virtualenv')
    sudo('apt-get install -y gunicorn')
    sudo('apt-get install -y supervisor')

def install_flask():
    """
    1. Create project directories
    2. Create and activate a virtualenv
    3. Copy Flask files to remote host
    """
    if exists(remote_app_dir) is False:
        sudo('mkdir ' + remote_app_dir)
    if exists(remote_flask_dir) is False:
        sudo('mkdir ' + remote_flask_dir)

    with cd(remote_app_dir):
            sudo('virtualenv env')
            sudo('source env/bin/activate')
            sudo('pip install Flask==0.10.1')
            sudo('pip install mysql-connector')
            sudo('pip install flask-wtf')
    with cd(remote_flask_dir):
        sudo("git clone "+git_repo_url+" .")

def configure_nginx():
    """

    2. Create new config file
    3. Setup new symbolic link
    4. Copy local config to remote config
    5. Restart nginx
    """
    sudo('/etc/init.d/nginx start')

    if exists('/etc/nginx/sites-enabled/flask_project') is False:
        sudo('touch /etc/nginx/sites-available/flask_project')
        sudo('ln -s /etc/nginx/sites-available/flask_project' + ' /etc/nginx/sites-enabled/flask_project')
    with lcd(local_config_dir):
        with cd(remote_nginx_dir):
            put('./flask_project', './', use_sudo=True)
    sudo('/etc/init.d/nginx restart')

def configure_supervisor():
    """
    1. Create new supervisor config file
    2. Copy local config to remote config
    3. Register new command
    """
    if exists('/etc/supervisor/conf.d/flask_project.conf') is False:
        with lcd(local_config_dir):
            with cd(remote_supervisor_dir):
                put('./flask_project.conf', './', use_sudo=True)
                sudo('supervisorctl reread')
                sudo('supervisorctl update')

def run_app():
    """ Run the app! """
    with cd(remote_flask_dir):
        sudo('supervisorctl start flask_project')

# run after going changes
def update_changes():
    """
    1. Copy new Flask files
    2. Restart gunicorn via supervisor
    """
    with cd(remote_flask_dir):
        sudo('git reset --hard HEAD')
        sudo('git pull')
        sudo('supervisorctl restart flask_project')

def status():
    """ Is our app live? """
    sudo('supervisorctl status')

def all_at_once():
    install_requirements()
    install_flask()
    configure_nginx()
    configure_supervisor()
    run_app()
