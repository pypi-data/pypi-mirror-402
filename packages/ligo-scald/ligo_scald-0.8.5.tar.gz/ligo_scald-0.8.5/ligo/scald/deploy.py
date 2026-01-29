import os
import shutil
import sys

from . import resources


CGI_BASH_TEMPLATE = """#!/bin/bash

export PYTHONPATH={python_path}:$PYTHONPATH
export SCALDRC_PATH={config_path}
exec python -m ligo.scald serve -b cgi -n {app_name} {cgi_extension}
"""


CGI_BASH_TEMPLATE_WITH_EGG = """#!/bin/bash

export PYTHON_EGG_CACHE=/tmp/{user}/.python-eggs
export PYTHONPATH={python_path}:$PYTHONPATH
export SCALDRC_PATH={config_path}
exec python -m ligo.scald serve -b cgi -n {app_name} {cgi_extension}
"""


def _add_parser_args(parser):
    parser.add_argument('-b', '--backend', default='cgi',
                        help="chooses server backend. options: [cgi]. default = cgi.")
    parser.add_argument('-c', '--config',
                        help="sets dashboard/plot options based on yaml configuration. if not set, uses SCALDRC_PATH.")
    parser.add_argument('-e', '--with-cgi-extension', default=False, action='store_true',
                        help="chooses whether scripts need to have a .cgi extension (if using cgi backend)")
    parser.add_argument('-o', '--output-dir', default=".",
                        help="chooses where web scripts and static files are deployed to (i.e. public_html)")
    parser.add_argument('-n', '--application-name', default='scald',
                        help="chooses the web application name. default = scald.")
    parser.add_argument('--add-egg-cache', default=False, action='store_true',
                        help="chooses whether to add PYTHON_EGG_CACHE variable to cgi script. default = False.")


def generate_cgi_script(config_path, output_dir, extension=False, script_name=None, egg_cache=False):
    if not script_name:
        script_name = os.path.splitext(os.path.basename(config_path))[0]
    if extension:
        script_name += '.cgi'
        cgi_extension = '-e'
    else:
        cgi_extension = ''
    if egg_cache:
        template = CGI_BASH_TEMPLATE_WITH_EGG
    else:
        template = CGI_BASH_TEMPLATE

    script_file = os.path.join(output_dir, 'cgi-bin', script_name)

    ### write script to disk
    with open(script_file, 'w') as f:
        f.write(template.format(
            python_path=os.getenv('PYTHONPATH'),
            config_path=os.path.abspath(config_path),
            cgi_extension=cgi_extension,
            app_name=os.path.splitext(script_name)[0],
            user=os.getenv('USER'),
        ))

    ### change permissions so it can be executed by web server
    os.chmod(script_file, 0o755)


def main(args=None):
    """Deploys a web application

    """
    if not args:
        parser = argparse.ArgumentParser()
        _parser_add_arguments(parser)
        args = parser.parse_args()

    server_backend = args.backend
    output_dir = args.output_dir
    extension = args.with_cgi_extension
    app_name = args.application_name
    egg_cache = args.add_egg_cache

    ### load configuration
    if args.config:
        config_path = args.config
    else:
        config_path = os.getenv('SCALDRC_PATH')
    if not config_path:
        raise KeyError('no configuration file found, please set your SCALDRC_PATH correctly or add --config param')

    ### generate web scripts
    if server_backend == 'cgi':
        generate_cgi_script(config_path, output_dir, extension=extension, script_name=app_name, egg_cache=egg_cache)

    ### copy over static files
    static_dir = resources.get_resource_path('static')
    try:
        if sys.version_info >= (3, 8):
            shutil.copytree(static_dir, os.path.join(output_dir, 'static'), dirs_exist_ok=True)
        else:
            # fallback for Python < 3.8
            from distutils import dir_util
            dir_util.copy_tree(static_dir, os.path.join(output_dir, 'static'))
    except OSError:
        pass
