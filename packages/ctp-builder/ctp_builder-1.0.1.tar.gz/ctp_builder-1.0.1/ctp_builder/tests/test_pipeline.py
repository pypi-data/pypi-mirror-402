from ctp_builder import CTPProject


def test_pipeline_default_values():
    pass


def test_passthrough_pipeline():
    project_config = {
        "version": 2,
        "template": "passthrough_service",
        "server": {
            "port": 8080,
            "storage": "/mnt/data",
        },
        "pipeline": {
            "name": "passthrough",
            "import_type": "Http",
            "import_port": 80,
            "export_type": "Dicom",
            "export_url": "dicom://XNAT:CTP@radiology-prod-xnat-dicom:8104",
        },
    }
    project = CTPProject()
    project.load_config(project_config)
    result = """<Configuration>
<Server
    maxThreads="20"
    port="8080"/>
<Pipeline name="passthrough">
    <HttpImportService
        class="org.rsna.ctp.stdstages.HttpImportService"
        logConnections="rejected"
        name="HttpImport"
        port="80"
        quarantine="/mnt/data/quarantine/passthrough/HttpImport"
        root="/mnt/data/root/passthrough/HttpImport"/>
    <DicomExportService
        class="org.rsna.ctp.stdstages.DicomExportService"
        name="DicomExporter"
        quarantine="/mnt/data/quarantine/passthrough/DicomExporter"
        root="/mnt/data/root/passthrough/DicomExporter"
        throttle="100"
        interval="2500"
        url="dicom://XNAT:CTP@radiology-prod-xnat-dicom:8104"/>
</Pipeline>
</Configuration>"""
    assert result == project.pipeline.render()

def test_polling_pipeline():
    project_config = {
        "version": 2,
        "template": "passthrough_service",
        "server": {
            "port": 8080,
            "storage": "/mnt/data",
        },
        "pipeline": {
            "name": "polling_pipeline",
            "import_type": "PollingHttp",
            "import_url": "http://example.com/data",
            "export_type": "PolledHttp",
            "export_port": 9090,
            "export_accept_ips": ["127.0.0.1"],
        },
    }
    project = CTPProject()
    project.load_config(project_config)
    result = """<Configuration>
<Server
    maxThreads="20"
    port="8080"/>
<Pipeline name="polling_pipeline">
    <PollingHttpImportService
        class="org.rsna.ctp.stdstages.PollingHttpImportService"
        name="PollingHttpImportService"
        id="PollingHttpImportService"
        url="http://example.com/data"
        acceptDicomObjects="yes"
        acceptXmlObjects="no"
        acceptZipObjects="no"
        acceptFileObjects="no"
        root="/mnt/data/root/polling_pipeline/PollingHttpImportService"
        quarantine="/mnt/data/quarantine/polling_pipeline/PollingHttpImportService"/>
    <PolledHttpExportService
        class="org.rsna.ctp.stdstages.PolledHttpExportService"
        name="PolledHttpExportService"
        id="stage ID"
        port="9090"
        ssl="no"
        acceptDicomObjects="yes"
        acceptXmlObjects="no"
        acceptZipObjects="no"
        acceptFileObjects="no"
        quarantine="/mnt/data/quarantine/polling_pipeline/PolledHttpExportService"
        root="/mnt/data/root/polling_pipeline/PolledHttpExportService"
        <accept ip="127.0.0.1"/>/>
</Pipeline>
</Configuration>"""
    assert result == project.pipeline.render()