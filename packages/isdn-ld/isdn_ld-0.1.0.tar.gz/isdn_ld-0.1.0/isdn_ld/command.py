from os import PathLike

import click
from isal import igzip_threaded
from joblib.parallel import cpu_count

from . import __version__
from .mappers import RDFFormatType
from .mappers.isdn import ISDNXML2RDFMapper


@click.group()
def cli():
    pass


@cli.command()
def version():
    click.echo(f"isdn_ld/{__version__}")


@cli.command(help="Convert XML files to RDF")
@click.argument("xml_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("output_file", type=click.Path(writable=True))
@click.option(
    "--processes",
    "-p",
    type=int,
    default=max(1, cpu_count(only_physical_cores=True) - 1),
    help="Number of worker processes",
)
@click.option(
    "--io-threads",
    type=int,
    default=2,
    help="This is only valid if the '--compress' option is specified.",
)
@click.option(
    "--format",
    "-f",
    "_format",
    type=click.Choice([v.name for v in RDFFormatType]),
    default=RDFFormatType.nq.name,
)
@click.option("--compress", "-c", is_flag=True, help="Enable gzip compression")
def convert(
    xml_dir: PathLike,
    output_file: PathLike,
    processes: int,
    io_threads: int,
    _format: str,
    compress: bool,
):
    mapper = ISDNXML2RDFMapper(xml_dir)

    click.echo(f"output: {output_file}")
    click.echo("Running mapper ...")

    f = igzip_threaded.open(output_file, "wt", threads=io_threads) if compress else open(output_file, "w")
    mapper.run(n_jobs=processes, output=f, format_type=RDFFormatType[_format])
    f.close()
