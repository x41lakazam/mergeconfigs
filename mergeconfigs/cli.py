import yaml
from pathlib import Path
import click

from .config_builder import build_config


@click.command()
@click.option("--file", help="Config file to start with", prompt="Input file name")
#@click.option("--env", prompt="Environment") 
@click.option("--workdir", default=".", prompt="Work dir", help="Working directory") 
@click.option("--outfile", default="easyconfig_full_config.yaml", help="Output file", prompt="Output file")
def main(file, workdir, outfile):
    workdir = Path(workdir)
    outfile = workdir.joinpath(outfile)
    config_d = build_config(workdir=workdir, filename=file)
    yaml.dump(config_d, open(outfile, 'w'))



