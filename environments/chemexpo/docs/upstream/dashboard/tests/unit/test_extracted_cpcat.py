import pytest

from dashboard.models import DataDocument, ExtractedCPCat
from dashboard.tests.loader import load_model_objects


@pytest.mark.loader
class TestCPCat:
    @pytest.fixture(autouse=True, scope="function")
    def _setup(self, django_db_setup):
        self.objects = load_model_objects()

    def test_cpcat_creation(self):
        cpdoc = DataDocument.objects.create(
            title="test CPCat document",
            data_group=self.objects.dg,
            document_type=self.objects.dt,
            filename="example.pdf",
        )

        cpc = ExtractedCPCat.objects.create(
            prod_name="test prod",
            cat_code="catcode",
            description_cpcat="Test Extracted CPCat Record",
            cpcat_code="excpcat",
            cpcat_sourcetype="sourcetype",
            data_document=cpdoc,
            extraction_script=self.objects.exscript,
        )
        assert cpc.__str__() == cpdoc.title
