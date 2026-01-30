import os

from .stages import ScriptTemplate


def generate_scripts(scripts_dir, scripts, scripts_config, output_dir):
    os.makedirs(output_dir/"scripts", exist_ok=True)
    for script_name in scripts:
        script_template = ScriptTemplate(script_name, scripts_dir)
        with open(output_dir / "scripts" / script_name, "w+") as output_script_file:
            output_script_file.write(script_template.render(**scripts_config))
