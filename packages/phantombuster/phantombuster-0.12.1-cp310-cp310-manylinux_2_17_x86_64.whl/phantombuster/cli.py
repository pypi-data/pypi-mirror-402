#!/usr/bin/env python

import logging
import logging.config
import os
import os.path
import sys
import multiprocessing as mp
import glob

import ntpath
from dataclasses import dataclass
import json

from phantombuster import porcelain, plumbing, stores
from phantombuster import core
from phantombuster.stores import deduplicator_to_pyarrow_table
from phantombuster.remoter import Worker
from phantombuster.io_ import write_parquet
from phantombuster.project import Project
import click
from typing import Optional, List
import pyarrow.parquet
import pyarrow.csv

from pathlib import Path

def configure_logging(outputlog, verbose):
    logging_config = {
                      'version': 1,
                      'formatters':{'default': {'format': "%(asctime)s %(levelname)-8s %(name)-15s %(message)s",
                                                'datefmt': "%Y-%m-%d %H:%M:%S"}},
                      'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'default', 'stream': 'ext://sys.stdout'}},
                      'loggers': {'remoter': {'level': 'WARNING'}},
                      'root': {'handlers': ['console'], 'level': 'INFO'}
                      }
    if outputlog:
        logging_config['handlers']['file'] = {'class': 'logging.FileHandler', 'formatter': 'default', 'filename': outputlog}
        logging_config['root']['handlers'].append('file')
    if verbose:
        logging_config['root']['level'] = 'DEBUG'

    logging.config.dictConfig(logging_config)
    logging.info('Logging configured')


def log_call(function, **kwargs):
    """Log a CLI call with all arguments"""
    logging.info(f"PhantomBuster {function} was called with the following arguments: {kwargs}")


@click.group()
@click.version_option(package_name='phantombuster')
@click.option("--verbose/--silent", default=False, help="Enable verbose debugging")
@click.option("-o", "--outputlog", type=click.Path(), help="Output file for logs")
@click.option("--save-results/--no-save-results", type=bool, default=True, help="DEBUG OPTION set no-save-results to not save which stages were already done")
def phantombuster(verbose: bool, outputlog: str, save_results: bool) -> None:
    print('configuring logging')
    configure_logging(outputlog, verbose)
    print('configured logging')


# -- Main Commands -- #


@phantombuster.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--outdir", required=True)
@click.option("--regex-file", required=True)
@click.option("--barcode-hierarchy-file", type=click.Path(exists=True), required=True)
@click.option("--debug/--production", default=False)
@click.option("--show-qc/--no-qc", default=False)
@click.option("--force/--no-force", default=False)
def demultiplex(input, regex_file, debug, outdir, show_qc, force, barcode_hierarchy_file):
    print('start demultiplex CLI command')
    log_call("demultiplex", input=input, regex_file=regex_file, debug=debug,
             outdir=outdir, show_qc=show_qc, barcode_hierarchy_file=barcode_hierarchy_file)
    project = Project(outdir)

    print('logged call, on to work')
    try:
        core.demultiplex(input, regex_file, barcode_hierarchy_file, project, debug=debug, show_qc=show_qc)
    except Exception as e:
        logging.exception("Pipeline encountered an error. Aborting.")
        raise click.Abort()
    return


@phantombuster.command()
@click.option("--outdir", required=True)
@click.option("--error-threshold", default=1)
@click.option("--barcode-hierarchy-file", required=True)
def error_correct(outdir, error_threshold, barcode_hierarchy_file):
    log_call("error-correct", outdir=outdir, error_threshold=error_threshold)
    project = Project(outdir)
    core.error_correct(project, error_threshold, barcode_hierarchy_file)


@phantombuster.command()
@click.argument('hopping-barcodes', nargs=-1)
@click.option("--outdir", required=True)
@click.option("--threshold", default=0.05, type=float)
def hopping_removal(outdir, threshold, hopping_barcodes):
    log_call("hopping-removal", outdir=outdir, threshold=threshold, hopping_barcodes=hopping_barcodes)
    project = Project(outdir)
    hopping_barcodes = [bc.split(',') for bc in hopping_barcodes]
    core.hopping_removal(project, hopping_barcodes, threshold)

@phantombuster.command()
@click.option("--outdir", required=True)
@click.option("--prefix")
@click.option("--threshold-file", required=True)
def threshold(outdir, prefix, threshold_file):
    log_call("threshold", outdir=outdir, prefix=prefix, threshold_file=threshold_file)
    core.threshold(outdir, prefix, threshold_file)

# -- Helper Commands -- #

@phantombuster.command()
@click.argument("prefixes", nargs=-1)
@click.option("--outdir", required=True)
@click.option("--prefix")
@click.option("--barcode-hierarchy-file", type=click.Path(exists=True), required=True)
def merge(prefixes, outdir, prefix, barcode_hierarchy_file):
    """
    Merge multiple prefixes under one prefix
    """
    # Log the call of this function with all parameters to the logfile
    log_call("merge", prefixes=prefixes, outdir=outdir, prefix=prefix, barcode_hierarchy_file=barcode_hierarchy_file)

    master_paths = PathsAndFiles(outdir, prefix, None)
    master_paths.create()

    try:
        barcode_hierarchy = plumbing.read_barcode_hierarchy_file(barcode_hierarchy_file)
    except Exception:
        raise Exception("Could not read barcode hierarchy file correctly")

    to_merge = [PathsAndFiles(outdir, prefix, None) for prefix in prefixes]

    results = [stores.load(('deduplication', True), paths.stage_path('deduplication')) for paths in to_merge]
    out = plumbing.combine(results, barcode_hierarchy)

    stores.save(out, master_paths.stage_path('deduplication'), id='deduplication')



@phantombuster.command()
@click.argument("parquetfile")
@click.argument("outfile", default=None, required=False)
def to_csv(parquetfile, outfile):
    log_call("to_csv", sample=parquetfile, outdir=outfile)
    table = pyarrow.parquet.read_table(parquetfile)
    if outfile is None:
        outfile = parquetfile.replace(".parquet", ".csv")
    pyarrow.csv.write_csv(table, outfile)


@phantombuster.command()
@click.argument("csvfile")
@click.argument("outfile", default=None, required=False)
def to_parquet(csvfile, outfile):
    log_call("to_parquet", csvfile=csvfile, outfile=outfile)
    table = pyarrow.csv.read_csv(csvfile)
    if outfile is None:
        outfile = csvfile.replace(".csv", ".parquet")
    write_parquet(table, outfile)


@phantombuster.command()
@click.option("--outdir", default=None, required=True)
@click.option("--name", default=None)
def worker(outdir, name):
    import phantombuster as phantombuster
    import phantombuster.plumbing

    project = Project(outdir)
    project.create()
    path = project._get_server_path()

    print(f"Connecting to {path}")
    worker = Worker(path, name=name)
    worker.start_async()

if __name__ == "__main__":
    phantombuster()
