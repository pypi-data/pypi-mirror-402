import logging
import textwrap

import yaml
from jinja2 import BaseLoader, Environment, PackageLoader, FileSystemLoader


class Config:
    def __init__(self, elements=None):
        self.elements = elements


class BaseElement:
    def __init__(self, name, root, quarantine):
        self.name = name
        self.root = root + '/' + self.name
        self.quarantine = quarantine + '/' + self.name
        logging.info(self)
        logging.debug(self.debug_str())

    def __str__(self) -> str:
        return f'{type(self).__name__} - {self.name}'

    def debug_str(self) -> str:
        attributes = []
        for attr, value in self:
            attributes.append(f'{attr}: {value}')
        return f'{self}\n'+'\n'.join(attributes)

    def config_str(self):
        raise NotImplementedError("config_str() method must be defined in a subclass")

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value

    def render(self):
        return textwrap.dedent(self.config_str()).strip()


class LookupTable:
    def __init__(self, filename="lookuptable.properties", values=None):
        self.filename = filename
        self.values = values

    def render(self):
        output = ""
        for lut_id, mapping in self.values.items():
            for key, val in mapping.items():
                output += f"{lut_id}/{key}={val}\n"
        return output


class ScriptTemplate:
    def __init__(self, script_name, env):
        logging.debug(f"Loading script template {script_name}...")
        self.template = env.get_template(script_name)

    def render(self, script_config=None):
        return self.template.render(**script_config)


class ProjectTemplate:
    def __init__(self,
                template_name,
                env):
        logging.debug(f"Loading template {template_name}.yaml")
        self.template = env.get_template(template_name + '.yaml')

    def render(self, template_config) -> str:
        return self.template.render(**template_config)


class Pipeline:
    def __init__(self, meta=None, stages=None, server_config=None):
        self.meta = meta
        self.stages = stages
        self.server_config = server_config

    def generate_meta(self, instance_pipeline_config) -> dict:
        return {
                "name": instance_pipeline_config.get("name") or "Pipeline",
                "author": instance_pipeline_config.get("author") or "CTP Admin",
                "version": instance_pipeline_config.get("version") or "1.0"
        }

    def generate_stages(self, stages_config=None):

        stages = list()

        for stage_name, stage_config in stages_config.items():
            if 'type' not in stage_config:
                logging.error(f"Error in generating pipeline. Stage '{stage_name}' is missing 'type'")
                return
            stage_type = stage_config.pop('type')
            stage_class = stage_classes.get(stage_type)
            if stage_class is None:
                logging.error(f"Error in generating pipeline. Stage type '{stage_type}' is not recognized")
                return
            stages.append(stage_class(**stage_config))

        return stages

    def from_config(self, pipeline_config):
        logging.debug("Loading pipeline config:")
        logging.debug("\n" + yaml.dump(pipeline_config, indent=2))

        logging.debug("Generating stages:")
        logging.debug(f"{', '.join(pipeline_config['stages'])}")

        self.stages = self.generate_stages(pipeline_config['stages'])

        if 'server' in pipeline_config:
            logging.debug("Generating server config")
            self.server_config = Server(**pipeline_config['server'])
        else:
            self.server_config = Server()

        self.meta = self.generate_meta(pipeline_config)

    def render_stages(self) -> str:
        return "\n".join([stage.render() for stage in self.stages])

    def render(self) -> str:

        template_string = textwrap.dedent(
            """\
            <Configuration>
            {{ server_config }}
            <Pipeline name="{{pipeline_name}}">
            {{pipeline | indent(4, True)}}
            </Pipeline>
            </Configuration>
            """)
        template = Environment(loader=BaseLoader()).from_string(template_string)

        return template.render({'pipeline': self.render_stages(), 'server_config': self.server_config.render(), 'pipeline_name': self.meta['name']})


class Server:
    def __init__(self, maxthreads=20, port=1080):
        self.maxthreads = maxthreads
        self.port = port

    def render(self) -> str:
        return textwrap.dedent(
        f"""\
        <Server
            maxThreads="{self.maxthreads}"
            port="{self.port}"/>""")


class Anonymizer(BaseElement):

    instances = 0

    def __init__(self,
                 id = None,
                 name="DicomAnonymizer",
                 lookup_table_location="resources/lookuptable",
                 quarantine="/data/quarantines/CTP1/DicomAnonymizer",
                 root="/data/roots/CTP1/DicomAnonymizer",
                 script="scripts/DicomAnonymizer.script"):
        if id is None:
            Anonymizer.instances += 1
            self.id = f"DicomAnonymizer{Anonymizer.instances}"
        else:
            self.id = id
        self.lookup_table_location = lookup_table_location
        self.script = script
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f'''
        <DicomAnonymizer
            id = "{self.id}"
            class="org.rsna.ctp.stdstages.DicomAnonymizer"
            lookupTable="{self.lookup_table_location}"
            name="{self.name}"
            quarantine="{self.quarantine}"
            root="{self.root}"
            script="{self.script}"/>
        ''')


class Corrector(BaseElement):
    def __init__(self,
                 name="DicomCorrector",
                 quarantine="/data/quarantines/CTP1/DicomCorrector",
                 root="/data/roots/CTP1/DicomCorrector"):
        self.quarantine = quarantine
        self.root = root
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <DicomCorrector
            class="org.rsna.ctp.stdstages.DicomCorrector"
            logUncorrectedMismatches="yes"
            name="{self.name}"
            quarantine="{self.quarantine}"
            root="{self.root}"/>
        """)


class DicomExport(BaseElement):
    def __init__(self,
                 type="DicomImport",
                 name="DicomExporter",
                 quarantine="/data/quarantines/CTP1/DicomExporter",
                 root="/data/roots/CTP1/DicomExporter",
                 throttle=100,
                 interval=2500,
                 url="localhost"):
        self.quarantine = quarantine
        self.root = root
        self.throttle = throttle
        self.interval = interval
        self.url = url
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <DicomExportService
            class="org.rsna.ctp.stdstages.DicomExportService"
            name=\"{self.name}\"
            quarantine="{self.quarantine}"
            root="{self.root}"
            throttle="{self.throttle}"
            interval="{self.interval}"
            url="{self.url}"/>
        """)


class HttpExport(BaseElement):
    def __init__(self,
                 name="HttpExporter",
                 quarantine="/data/quarantines/CTP1/DicomExporter",
                 root="/data/roots/CTP1/DicomExporter",
                 interval=2500,
                 url="localhost"):
        self.quarantine = quarantine
        self.root = root
        self.interval = interval
        self.url = url
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <HttpExportService
            class="org.rsna.ctp.stdstages.HttpExportService"
            name="{self.name}"
            quarantine="{self.quarantine}"
            root="{self.root}"
            interval="{self.interval}"
            url="{self.url}"/>
        """)


class DirectoryExport(BaseElement):
    def __init__(self,
                 name="DirectoryExport",
                 quarantine="/data/quarantines/CTP1/DirectoryExport",
                 root="/data/roots/CTP1/DirectoryExport",
                 path="/data/sorted",
                 structure="(0010,0020)/(0008,0020)/0020,000d/(0008,103e)"):
        self.quarantine = quarantine
        self.path = path
        self.structure = structure
        super().__init__(name, root, quarantine)
        self.root = root

    def config_str(self) -> str:
        return (
        f"""
        <DirectoryStorageService
            class="org.rsna.ctp.stdstages.DirectoryStorageService"
            name="{self.name}"
            quarantine="{self.quarantine}"
            root="{self.root}"
            structure="{self.structure}"
            path="{self.path}"/>    
        """)


class FileExport(BaseElement):
    def __init__(self,
                 name="FileExport",
                 quarantine="/data/quarantines/CTP1/FileExport",
                 root="/data/roots/CTP1/FileExport",
                 path="/data/unsorted"):
        self.quarantine = quarantine
        self.root = root
        self.path = path
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <FileStorageService
            class="org.rsna.ctp.stdstages.FileStorageService"
            name="{self.name}"
            quarantine="{self.quarantine}"
            root="{self.root}"
            exportDirectory="{self.path}"/>    
        """)


class PolledHttpExportService(BaseElement):
    def __init__(self,
                 name="PolledHttpExportService",
                 id="stage ID",
                 port="8080",
                 ssl="no",
                 quarantine="/data/quarantines/CTP1/PolledHttpExportService",
                 root="/data/roots/CTP1/PolledHttpExportService",
                 accept_ips=[]
                 ):
        self.id = id
        self.port = port
        self.ssl = ssl
        self.accept_ips = accept_ips
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        accepet_ips_str = "\n".join([f'<accept ip="{ip}"/>' for ip in self.accept_ips])
        return (
        f"""
        <PolledHttpExportService
            class="org.rsna.ctp.stdstages.PolledHttpExportService"
            name="{self.name}"
            id="{self.id}"
            port="{self.port}"
            ssl="{self.ssl}"
            acceptDicomObjects="yes"
            acceptXmlObjects="no"
            acceptZipObjects="no"
            acceptFileObjects="no"
            quarantine="{self.quarantine}"
            root="{self.root}"
            {accepet_ips_str}/>
        """)


class Filter(BaseElement):
    def __init__(self,
                 type="Filter",
                 name="DicomFilter",
                 script="DicomFilter.script",
                 quarantine="/data/quarantines/CTP1/DicomFilter",
                 root="/data/roots/CTP1/DicomFilter",
                 template="filter.xml"):
        self.script = script
        self.template = template
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <DicomFilter
            class="org.rsna.ctp.stdstages.DicomFilter"
            name="{self.name}"
            quarantine="{self.quarantine}"
            root="{self.root}"
            script="{self.script}"/>
        """)


class DicomImport(BaseElement):
    def __init__(self,
                 type="DicomImport",
                 name="DicomImport",
                 ip="127.0.0.1",
                 port="80",
                 quarantine="/data/quarantines/CTP1/DicomImportService",
                 root="/data/roots/CTP1/DicomImportService"):
        self.ip = ip
        self.port = port
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <DicomImportService
            class="org.rsna.ctp.stdstages.DicomImportService"
            logConnections="rejected"
            name="{self.name}"
            port="{self.port}"
            quarantine="{self.quarantine}"
            root="{self.root}"/>
        """)


class HttpImport(BaseElement):
    def __init__(self,
                 name="HttpImport",
                 ip="127.0.0.1",
                 port="80",
                 quarantine="/data/quarantines/CTP1/HttpImport",
                 root="/data/roots/CTP1/HttpImport"):
        self.ip = ip
        self.port = port
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <HttpImportService
            class="org.rsna.ctp.stdstages.HttpImportService"
            logConnections="rejected"
            name="{self.name}"
            port="{self.port}"
            quarantine="{self.quarantine}"
            root="{self.root}"/>
        """)


class ArchiveImport(BaseElement):
    def __init__(self,
                 name="ArchiveImport",
                 path="/data/archive",
                 quarantine="/data/quarantines/CTP1/ArchiveImport",
                 root="/data/roots/CTP1/ArchiveImport"):
        self.path = path
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <ArchiveImportService
            class="org.rsna.ctp.stdstages.ArchiveImportService"
            logConnections="rejected"
            name="{self.name}"
            treeRoot="{self.path}"
            quarantine="{self.quarantine}"
            root="{self.root}"
            acceptDicomObjects="yes"/>
        """)


class DirectoryImport(BaseElement):
    def __init__(self,
                 name="DirectoryImport",
                 path="/data/archive",
                 quarantine="/data/quarantines/CTP1/DirectoryService",
                 root="/data/roots/CTP1/DirectoryService"):
        self.path = path
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <DirectoryImportService
            name="{self.name}"
            class="org.rsna.ctp.stdstages.DirectoryImportService"
            root="{self.root}"
            quarantine="{self.quarantine}"
            import="{self.path}"
            interval="20000"
            acceptDicomObjects="yes"
            acceptXmlObjects="yes"
            acceptZipObjects="yes"
            acceptFileObjects="yes"/>   
        """)

class PollingHttpImportService(BaseElement):
    def __init__(self,
                 name="PollingHttpImportService",
                 url="",
                 quarantine="/data/quarantines/CTP1/PollingHttpImportService",
                 root="/data/roots/CTP1/PollingHttpImportService"):
        self.url = url
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <PollingHttpImportService
            class="org.rsna.ctp.stdstages.PollingHttpImportService"
            name="PollingHttpImportService"
            id="PollingHttpImportService"
            url="{self.url}"
            acceptDicomObjects="yes"
            acceptXmlObjects="no"
            acceptZipObjects="no"
            acceptFileObjects="no"
            root="{self.root}"
            quarantine="{self.quarantine}"/>
        """)

class PixelAnonymizer(BaseElement):
    def __init__(self,
                 name="DicomPixelAnonymizer",
                 quarantine="/data/quarantines/CTP1/DicomPixelAnonymizer",
                 root="/data/roots/CTP1/DicomPixelAnonymizer",
                 script="scripts/DicomPixelAnonymizer.script"):
        self.script = script
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <DicomPixelAnonymizer
            class="org.rsna.ctp.stdstages.DicomPixelAnonymizer"
            log="yes"
            name="{self.name}"
            quarantine="{self.quarantine}"
            root="{self.root}"
            script="{self.script}"/>
        """)


class LookupTableChecker(BaseElement):
    def __init__(self,
                 id="LookupTableChecker",
                 name="LookupTableChecker",
                 quarantine="/data/quarantines/CTP1/LookupTableChecker",
                 root="/data/roots/CTP1/LookupTableChecker"):
        self.id = id
        super().__init__(name, root, quarantine)

    def config_str(self) -> str:
        return (
        f"""
        <LookupTableChecker
            class="org.rsna.ctp.stdstages.LookupTableChecker"
            id="{self.id}"
            name="{self.name}"
            quarantine="{self.quarantine}"
            root="{self.root}"/>
        """)


class ObjecTracker(BaseElement):
    def __init__(self,
                 id="ObjectTracker",
                 name="ObjectTracker",
                 root="/data/roots/CTP1/ObjectTracker"):
        self.id = id
        super().__init__(name, root, "")

    def config_str(self) -> str:
        return (
        f"""
        <ObjectTracker
            name="{self.name}"
            class="org.rsna.ctp.stdstages.ObjectTracker"
            root="{self.root}" />
        """)


class IDMap(BaseElement):
    def __init__(self,
                 id="IDMap",
                 name="IDMap",
                 root="/data/roots/CTP1/IDMap"):
        self.id = id
        super().__init__(name, root, "")

    def config_str(self) -> str:
        return (
        f"""
        <IDMap
            name="{self.name}"
            class="org.rsna.ctp.stdstages.IDMap"
            root="{self.root}"/>
        """)


stage_classes = {
    'DicomImport': DicomImport,
    'HttpImport': HttpImport,
    'ArchiveImport': ArchiveImport,
    'DirectoryImport': DirectoryImport,
    'PollingHttpImport': PollingHttpImportService,
    'DicomExport': DicomExport,
    'HttpExport': HttpExport,
    'FileExport': FileExport,
    'DirectoryExport': DirectoryExport,
    'PolledHttpExport': PolledHttpExportService,
    'Anonymizer': Anonymizer,
    'Corrector': Corrector,
    'Filter': Filter,
    'PixelAnonymizer': PixelAnonymizer,
    'ObjectTracker': ObjecTracker,
    'LookupTableChecker': LookupTableChecker,
}
