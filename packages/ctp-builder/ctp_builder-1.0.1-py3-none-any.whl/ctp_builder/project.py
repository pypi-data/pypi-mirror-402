import logging
import os
import zipfile

import yaml
from jinja2 import BaseLoader, Environment, PackageLoader, FileSystemLoader

from .stages import LookupTable, Pipeline, ProjectTemplate, ScriptTemplate


class CTPProject:
    def __init__(self, label="CTP Project", pipeline=None, scripts=None, lookup_table=None):
        self.label = label
        self.pipeline = pipeline
        self.scripts = scripts
        self.lookup_table = lookup_table

    def generate_scripts(self, scripts_config, env):
        scripts_to_include = scripts_config.pop("include")
        scripts = dict()
        for script_name in scripts_to_include:
            script_template = ScriptTemplate(script_name, env)
            scripts[script_name] = script_template.render(scripts_config)
        return scripts

    def load_config(self, config, templates_dir=None):
        # If templates_dir not set use package templates
        if templates_dir:
            project_env = Environment(loader=FileSystemLoader(templates_dir))
            scripts_env = Environment(loader=FileSystemLoader(templates_dir / 'scripts'))
        else:
            project_env = Environment(loader=PackageLoader("ctp_builder", "resources/templates/projects"))
            scripts_env = Environment(loader=PackageLoader("ctp_builder", "resources/scripts"))

        if 'template' in config:
            project_template = ProjectTemplate(config.pop("template"), project_env)
        else:
            raise ValueError("Project template is not found!")

        logging.debug(f"Using template: {project_template}")
        # logging.debug("\n" + yaml.dump(project_template.template, indent=2))

        project_instance_config = yaml.safe_load(project_template.render(config))
        logging.debug(f'Project instance config:')
        logging.debug(f'\n' + yaml.dump(project_instance_config, indent=2))
        
        if "pipeline" in project_instance_config:
            pipeline_config = project_instance_config.pop("pipeline")
            self.pipeline = Pipeline()
            self.pipeline.from_config(pipeline_config)

        if 'scripts' in project_instance_config:
            logging.info("Generating scripts")
            self.scripts = self.generate_scripts(project_instance_config.pop("scripts"), scripts_env)
            for script_name, script_content in self.scripts.items():
                logging.debug(f'{script_name}:')
                logging.debug(script_content)

        if 'project' in project_instance_config and 'lookuptable' in project_instance_config['project']:
            lut_conf = project_instance_config['project']['lookuptable']
            self.lookup_table = LookupTable(filename=lut_conf['name'], values=lut_conf['fields'])

    def save(self, output_dir):

        if self.pipeline is not None:
            with open(output_dir/'config.xml', 'w') as config_file:
                config_file.write(self.pipeline.render())

        if self.scripts is not None:
            os.makedirs(output_dir/'scripts', exist_ok=True)
            for name, script in self.scripts.items():
                with open(output_dir/'scripts'/name, 'w') as scripts_file:
                    scripts_file.write(script)

        if self.lookup_table is not None:
            with open(self.lookup_table.filename, 'w') as lut_file:
                lut_file.write(self.lookup_table.render())

    def save_to_zipfile(self, output_filename):
        with zipfile.ZipFile(output_filename, 'w') as project_file:
            if self.pipeline is not None:
                project_file.writestr(self.name/"config.xml", self.pipeline.render())
            if self.scripts is not None:
                for name, script in self.scripts.items():
                    project_file.writestr(self.name/'scripts'/name, script)
            if self.lookup_table is not None:
                project_file.writestr(self.name/self.lookup_table.filename, self.lookup_table.render())
