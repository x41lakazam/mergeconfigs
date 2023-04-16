import yaml
from pathlib import Path
import click

from .config_builder import build_config


@click.command()
@click.option("--file", help="Config file to start with", prompt="Input file name")
@click.option("--env", prompt="Environment", default=".")
@click.option("--workdir", default=".", prompt="Work dir", help="Working directory")
@click.option("--outfile", default="easyconfig_full_config.yaml", help="Output file", prompt="Output file")
@click.option("--hierarchy", default=None, prompt="Hierarchy file", help="Hierarchy descriptor file")
def main(file, workdir, outfile, env, hierarchy):
    workdir = Path(workdir)

    outfile = workdir.joinpath(outfile)
    config_d = build_config(workdir=workdir, filename=file, env=env, hierarchy_filename=hierarchy)
    yaml.dump(config_d, open(outfile, 'w'))



