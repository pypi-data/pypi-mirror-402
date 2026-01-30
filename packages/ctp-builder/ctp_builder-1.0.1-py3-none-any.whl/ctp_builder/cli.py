import csv
import logging
import os
import socket
from pathlib import Path

import click
import requests
import yaml
from click_loglevel import LogLevel

from .project import CTPProject


@click.group()
@click.version_option()
@click.option('--log-level', type=LogLevel(), default=logging.INFO)
@click.pass_context
def cli(ctx, log_level):
    logging.basicConfig(
        format=f"%(asctime)s - {socket.gethostname()} - [%(levelname)-8s] %(message)s",
        level=log_level,
    )
    ctx.ensure_object(dict)


@cli.command()
@click.option('--config', type=Path, required=True)
@click.option('--output-dir', type=Path, required=True)
@click.option('--templates', type=Path, required=False)
@click.pass_context
def generate(ctx, config, output_dir, templates):
    if not os.path.isdir(output_dir):
        logging.error(f"Directory '{output_dir}' does not exist, creating folder")
        os.mkdir(output_dir)

    logging.info('Reading config')

    with open(config) as conf_file:
        project_config = yaml.safe_load(conf_file)

    logging.debug(f"Pipeline config filename: :{config}")
    logging.debug("Pipeline config:")
    logging.debug("\n" + yaml.dump(project_config, indent=2))

    project = CTPProject()
    project.load_config(project_config, templates)
    project.save(output_dir)


@cli.command()
@click.option('--lookup-table-filename', type=Path, required=True)
@click.option('--ctp-host', required=True)
@click.option('--ctp-port', type=int, default=1180, required=True)
@click.option('--dicom-anonymizer-id', required=True)
@click.option('--username', required=True)
@click.option('--password', required=True, prompt=True, hide_input=True)
@click.option('--log-level', type=LogLevel(), default=logging.INFO)
@click.pass_context
def post_lookup_table(ctx, lookup_table_filename, ctp_host, ctp_port, dicom_anonymizer_id, username, password, log_level):
    logging.basicConfig(
        format=f"%(asctime)s - {socket.gethostname()} - [%(levelname)-8s] %(message)s",
        level=log_level,
    )
    with open(lookup_table_filename) as lookup_table_file:
        kvreader = csv.reader(lookup_table_file)
        for row in kvreader:
            headers = {'RSNA': f'{username}:{password}'}
            response = requests.put(f"{ctp_host}:{ctp_port}/lookup?id={dicom_anonymizer_id}&key={row[0]}&value={row[1]}", headers=headers)
            logging.debug(response.content)
