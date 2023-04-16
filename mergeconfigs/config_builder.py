from typing import List, Optional
from itertools import pairwise
import collections.abc
from pathlib import Path
import re
import yaml
from yaml import Loader


VAR_REGEX = r"\${(\w+@[.\w]+)}"


def _dic_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = _dic_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def _get_var(var_name, ctx):
    """var_name is in format file@variable"""
    try:
        in_file, var = var_name.split("@")
    except ValueError:
        raise Exception(f"Bad variable name {var_name}")

    if in_file not in ctx:
        raise Exception(f"No such file {in_file}: {list(ctx.keys())}")

    v = ctx.get(in_file)
    subkeys = var.split(".")
    while subkeys:
        k = subkeys.pop(0)
        try:
            v = v[k]
        except:
            raise Exception(f"Bad subkey {k} in {var}")

    return v

def _resolve_variables(val, ctx):
    if isinstance(val, list):
        return [_resolve_variables(e, ctx) for e in val]
    elif isinstance(val, dict):
        return {k:_resolve_variables(v, ctx) for k,v in val.items()}

    if not isinstance(val, str):
        return val

    try:
        val = re.sub(VAR_REGEX, lambda m: str(_get_var(m.groups()[0], ctx)), val)
    except Exception as exc:
        print(f"Error on value {val}: {exc}")
        raise

    return val


def _resolve_yaml(file: Path, workdir=Path("."), env=".", ctx=None, callers=None):
    callers = callers or []
    ctx = ctx or {}

    file_content = yaml.load(open(file.absolute()), Loader=Loader) or {}

    # Store the content of the current file under "this" namespace
    inner_ctx = {"this": file_content}
    ctx = ctx | inner_ctx

    file_vars = file_content.copy()
    ctx[file.stem] = file_vars

    lines = open(file.absolute()).readlines()

    for line in lines:
        line = line.replace("$$ENV$$", env)
        if line.startswith("#extends"):
            extends_yaml = line.split(" ")[1].strip()
            fpath = workdir.joinpath(extends_yaml)
            extends_content = _resolve_yaml(fpath, workdir, env, ctx, callers + [file.stem])
            _dic_update(extends_content, file_content)
            file_content = extends_content

        elif line.startswith("#include"):
            include_yaml = line.split(" ")[1].strip()
            fpath = workdir.joinpath(include_yaml)
            if fpath.stem in callers:
                raise RecursionError(f"Circular import of {fpath.name} in {file.name}")
            include_content = _resolve_yaml(fpath, workdir, env, ctx, callers + [file.stem])
            common_keys = include_content.keys() & file_content.keys()
            if common_keys:
                print(f"WARNING: Included file {include_yaml} have common keys with parent file, overwriting: {common_keys}")

            file_content.update(include_content)

        elif line.startswith("#load"):
            load_yaml = line.split(" ")[1].strip()
            fpath = workdir.joinpath(load_yaml)
            if fpath.stem in callers:
                raise RecursionError(f"Circular import of {fpath.name} in {file.name}")
            content = _resolve_yaml(fpath, workdir, env, ctx, callers + [file.stem])
            ctx[fpath.stem] = content

    for k,v in file_content.items():
        file_content[k] = _resolve_variables(v, ctx)

    return file_content


def _fill_hierarchy_files(workdir: Path, hierarchy: List[str]) -> List[Path]:
    files_created = []

    # Gather every file that appear in at least one environment, names are relative to the env dir
    existing_files = set()
    for env in hierarchy:
        envdir = workdir.joinpath(env)
        existing_files |= set(f.relative_to(envdir) for f in envdir.rglob("*") if f.is_file())

    # In every env dir, create the file pointing to the upper environment if it doesn't exist
    for env, parent_env in pairwise(hierarchy[::-1]):     # Travel the hierarchy backward (from the leaf to the one before the root)
        envdir = workdir.joinpath(env)

        # Get every file that is missing
        files_in_env = set(f.relative_to(envdir) for f in envdir.rglob(f"*") if f.is_file)
        missing_filenames = existing_files - files_in_env

        # Create those files
        for f in missing_filenames:
            filepath = envdir.joinpath(f)
            filepath.open('w').write(f"#extends {parent_env}/{f}")
            files_created.append(filepath)

    return files_created



def build_config(filename="config.yaml", workdir=Path("."), env=".", hierarchy_filename: Optional[str] = None):
    tmp_files: List[Path] = []

    workdir = Path(workdir)
    file = workdir.joinpath(filename)

    # If hierarchy was provided, created the missing files
    if hierarchy_filename:
        hierarchy = workdir.joinpath(hierarchy_filename).open().read().splitlines()
        tmp_files += _fill_hierarchy_files(workdir, hierarchy)

    # Build the configuration dictionary
    full_config_dict = _resolve_yaml(file, workdir, env)

    # Remove temporary files
    for f in tmp_files:
        if f.exists():
            f.unlink()

    return full_config_dict
