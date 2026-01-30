from ctp_builder import stages


def test_default_filter():
    filter = stages.Filter()
    default_config = filter.render()
    assert default_config == \
'''<DicomFilter
    class="org.rsna.ctp.stdstages.DicomFilter"
    name="DicomFilter"
    quarantine="/data/quarantines/CTP1/DicomFilter/DicomFilter"
    root="/data/roots/CTP1/DicomFilter/DicomFilter"
    script="DicomFilter.script"/>'''


def test_filter_config_values():
    filter = stages.Filter(name="TestName",
                           script="TestScript.script",
                           quarantine="/test",
                           root="/test")
    config = filter.render()
    assert config == \
'''<DicomFilter
    class="org.rsna.ctp.stdstages.DicomFilter"
    name="TestName"
    quarantine="/test/TestName"
    root="/test/TestName"
    script="TestScript.script"/>'''


def test_DirectoryImport_config_values():
    filter = stages.DirectoryImport(name="TestName",
                                    path='/mnt/data/import',
                                    quarantine="/test",
                                    root="/test")
    config = filter.render()
    assert config == \
'''<DirectoryImportService
    name="TestName"
    class="org.rsna.ctp.stdstages.DirectoryImportService"
    root="/test/TestName"
    quarantine="/test/TestName"
    import="/mnt/data/import"
    interval="20000"
    acceptDicomObjects="yes"
    acceptXmlObjects="yes"
    acceptZipObjects="yes"
    acceptFileObjects="yes"/>'''


def test_polling_http_import_service():
    service = stages.PollingHttpImportService()
    default_config = service.render()
    assert default_config == \
'''<PollingHttpImportService
    class="org.rsna.ctp.stdstages.PollingHttpImportService"
    name="PollingHttpImportService"
    id="PollingHttpImportService"
    url=""
    acceptDicomObjects="yes"
    acceptXmlObjects="no"
    acceptZipObjects="no"
    acceptFileObjects="no"
    root="/data/roots/CTP1/PollingHttpImportService/PollingHttpImportService"
    quarantine="/data/quarantines/CTP1/PollingHttpImportService/PollingHttpImportService"/>'''

def test_polled_http_export_service():
    service = stages.PolledHttpExportService()
    default_config = service.render()
    assert default_config == \
'''<PolledHttpExportService
    class="org.rsna.ctp.stdstages.PolledHttpExportService"
    name="PolledHttpExportService"
    id="stage ID"
    port="8080"
    ssl="no"
    acceptDicomObjects="yes"
    acceptXmlObjects="no"
    acceptZipObjects="no"
    acceptFileObjects="no"
    quarantine="/data/quarantines/CTP1/PolledHttpExportService/PolledHttpExportService"
    root="/data/roots/CTP1/PolledHttpExportService/PolledHttpExportService"
    />'''

def test_polled_http_export_service_with_config():
    config={
        "id": "CustomID",
        "port": 9090,
        "ssl": "yes",
        "accept_ips": ["127.0.0.1"]
    }
    service = stages.PolledHttpExportService(**config)
    default_config = service.render()
    assert default_config == \
'''<PolledHttpExportService
    class="org.rsna.ctp.stdstages.PolledHttpExportService"
    name="PolledHttpExportService"
    id="CustomID"
    port="9090"
    ssl="yes"
    acceptDicomObjects="yes"
    acceptXmlObjects="no"
    acceptZipObjects="no"
    acceptFileObjects="no"
    quarantine="/data/quarantines/CTP1/PolledHttpExportService/PolledHttpExportService"
    root="/data/roots/CTP1/PolledHttpExportService/PolledHttpExportService"
    <accept ip="127.0.0.1"/>/>'''