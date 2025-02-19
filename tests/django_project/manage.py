#!/usr/bin/env python

""" Django's command-line utility for administrative tasks. """

from pathlib import Path
import os
import sys
import json


thisdir = Path(__file__).resolve().parent


class Env(dict):

    def __init__(self):
        self.prefix = ''

    def add(self, values: str):
        if self.prefix:
            if isinstance(values, str):
                for key in values.split(','):
                    self[f'{self.prefix}_{key}'] = ''
            elif isinstance(values, list):
                for key in values:
                    self[f'{self.prefix}_{key}'] = ''
            elif isinstance(values, dict):
                for key, val in values.items():
                    self[f'{self.prefix}_{key}'] = val

    def section(self, prefix: str, value: str = None):
        self.prefix = prefix
        if value is not None:
            self[prefix] = value

    def write(self, filename: Path):
        lines = [f'{key}={val}' for key, val in self.items()]
        filename.write_text('\n'.join(lines))


def write_envfile():
    try:
        from django.core.management.utils import get_random_secret_key
        secret_key = get_random_secret_key()
        i = 0
        while ('#' in secret_key) & (i < 300):
            secret_key = get_random_secret_key()
            i += 1
    except ImportError:
        raise ImportError('cannot import Django.')
    env = Env()
    env['DEBUG'] = 'on'
    env['HTTPS'] = 'off'
    env['DJANGO_SECRET_KEY'] = f'"{secret_key}"'
    env.section('AAD')
    env.add('CLIENT_ID,CLIENT_CREDENTIAL,AUTHORITY')
    env.section('AZURE_STORAGE', '')
    env.add('AZURE_STORAGE_CONTAINER')
    fil = thisdir / '.env'
    if not fil.exists():
        env.write(fil)
        print(f'please fill the file: {fil}')
    else:
        print(f'file already exists: {fil}')


def write_azureconfig():
    """ Write the Azure Web App Service Configuration in a JSON file """
    fil = thisdir / '.env'
    values = {}
    for line in fil.read_text().splitlines():
        lin = line.strip()
        p = lin.find('=')
        if p > 0:
            k = lin[0:p]
            v = lin[p+1:].strip('"')
            if not k.startswith('DOCKER_'):
                values[k] = v
    for k in list(values):
        v = values[k]
        if v.startswith('$'):
            i = v[1:]
            if i in values:
                values[k] = values[i]
    values['DEBUG'] = 'off'
    values['HTTPS'] = 'on'
    cfg = []
    for key, val in values.items():
        if not key.startswith('DOCKER_'):
            cfg.append(dict(name=key, value=val, slotSetting=False))
    fil = thisdir / 'azureconfig.json'
    fil.write_text(json.dumps(cfg, indent=2))
    msg = 'copy the content of the file in the Azure App Service '
    msg += f'Configuration\n>>> {fil}'
    print(msg)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':

    if 'envfile' in sys.argv:
        write_envfile()
    elif 'azureconfig' in sys.argv:
        write_azureconfig()
    else:
        main()
