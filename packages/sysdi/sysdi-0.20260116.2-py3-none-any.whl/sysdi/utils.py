from collections.abc import Iterable
from os import environ
import re
import subprocess


def sub_run(
    *args,
    capture=False,
    returns: None | Iterable[int] = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    kwargs.setdefault('check', not bool(returns))
    capture = kwargs.setdefault('capture_output', capture)
    args = args + kwargs.pop('args', ())
    env = kwargs.pop('env', None)
    if env:
        kwargs['env'] = environ | env
    if capture:
        kwargs.setdefault('text', True)

    try:
        result = subprocess.run(args, **kwargs)
        if returns and result.returncode not in returns:
            raise subprocess.CalledProcessError(result.returncode, args[0])
        return result
    except subprocess.CalledProcessError as e:
        if capture:
            print(e.stderr)
        raise


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9-]+', '-', text)  # replace non-alphanum (except dashes) with dash
    text = re.sub(r'-{2,}', '-', text)  # replace multiple dashes with one
    return text.strip('-')
