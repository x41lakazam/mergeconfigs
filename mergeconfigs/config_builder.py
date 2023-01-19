from pathlib import Path
import re
import yaml
from yaml import Loader


#VAR_REGEX = r"\${([^|]+?)}"
VAR_REGEX = r"\${(\w+@[.\w]+)}"

def _get_var(var_name, parent_vars):
    """var_name is in format file@variable"""
    try:
        in_file, var = var_name.split("@")
    except ValueError:
        raise Exception(f"Bad variable name {var_name}")

    if in_file not in parent_vars:
        raise Exception(f"No such file {in_file}: {list(parent_vars.keys())}")

    v = parent_vars.get(in_file)
    subkeys = var.split(".")
    while subkeys:
        k = subkeys.pop(0)
        try:
            v = v[k]
        except:
            raise Exception(f"Bad subkey {k} in {var}")

    return v

def _resolve_variables(val, content):
    if isinstance(val, list):
        return [_resolve_variables(e, content) for e in val]
    elif isinstance(val, dict):
        return {k:_resolve_variables(v, content) for k,v in val.items()}

    if not isinstance(val, str):
        return val

    try:
        val = re.sub(VAR_REGEX, lambda m: _get_var(m.groups()[0], content), val)
    except Exception as exc:
        print(f"Error on value {val}: {exc}")
        raise

    return val


def _resolve_yaml(file: Path, workdir=Path("."), env="base", parent_vars=None, callers=None):
    callers = callers or []
    parent_vars = parent_vars or {}

    file_content = yaml.load(open(file.absolute()), Loader=Loader)

    file_vars = file_content.copy()
    parent_vars[file.stem] = file_vars

    lines = open(file.absolute()).readlines()

    for line in lines:
        if line.startswith("#extends"):
            extends_yaml = line.split(" ")[1].strip()
            fpath = workdir.joinpath(extends_yaml)
            content = _resolve_yaml(fpath, workdir, env, parent_vars, callers+[file.stem])
            content.update(file_content)
            file_content = content

        elif line.startswith("#include"):
            include_yaml = line.split(" ")[1].strip()
            fpath = workdir.joinpath(include_yaml)
            if fpath.stem in callers:
                raise RecursionError(f"Circular import of {fpath.name} in {file.name}")
            content = _resolve_yaml(fpath, workdir, env, parent_vars, callers+[file.stem])
            file_content.update(content)

        elif line.startswith("#load"):
            load_yaml = line.split(" ")[1].strip()
            fpath = workdir.joinpath(load_yaml)
            if fpath.stem in callers:
                raise RecursionError(f"Circular import of {fpath.name} in {file.name}")
            content = _resolve_yaml(fpath, workdir, env, parent_vars, callers+[file.stem])
            parent_vars[fpath.stem] = content

    for k,v in file_content.items():
        file_content[k] = _resolve_variables(v, parent_vars)

    return file_content


def build_config(filename="config.yaml", workdir=Path("."), env="base"):


    workdir = Path(workdir)
    file = workdir.joinpath(filename)

    full_config_dict = _resolve_yaml(file, workdir, env)

    return full_config_dict
