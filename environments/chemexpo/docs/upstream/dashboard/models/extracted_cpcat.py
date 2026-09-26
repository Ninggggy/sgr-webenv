from django.db import models
from .extracted_text import ExtractedText
from .extracted_list_presence import ExtractedListPresence, ExtractedListPresenceTag


class ExtractedCPCat(ExtractedText):
    """
    This is the subclass of `dashboard.models.extracted_text.ExtractedText`
    that is created when a user uploads list presence data. Its child objects
    are of the `dashboard.models.extracted_list_presence.ExtractedListPresence` class.
    """

    cat_code = models.CharField("Cat code", max_length=100, blank=True)
    description_cpcat = models.CharField("CPCat cassette", max_length=200, blank=True)
    cpcat_code = models.CharField("ACToR snaid", max_length=50, blank=True)
    cpcat_sourcetype = models.CharField("CPCat source", max_length=50, blank=True)

    author = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Author",
        help_text="Author",
        default="",
    )

    doi = models.CharField(
        max_length=50, blank=True, verbose_name="DOI", help_text="DOI", default=""
    )

    def __str__(self):
        return str(self.data_document)

    @property
    def qa_begun(self):
        return (
            self.rawchem.select_subclasses()
            .filter(extractedlistpresence__qa_flag=True)
            .exists()
        )

    def get_tagset(self):
        """
        Given an ExtractedCPCat object, select all of the distinct
        ListPresenceTag records that have been assigned to its ExtractedListPresence
        child records
        """
        qs = (
            (
                ExtractedListPresenceTag.objects.filter(
                    extractedlistpresence__extracted_text__extractedcpcat=self
                )
            )
            .distinct()
            .order_by("name")
        )
        return qs

    def prep_cp_for_qa(self):
        """
        Given an ExtractedCPCat object, select a sample of its
        ExtractedListPresence children for QA review.
        """
        QA_RECORDS_PER_DOCUMENT = 30
        other_lps = None

        elps = self.rawchem.select_subclasses()
        flagged = elps.filter(extractedlistpresence__qa_flag=True).count()
        # if less than 30 records not flagged for QA, count of ALL may be < 30
        if flagged < QA_RECORDS_PER_DOCUMENT and flagged < elps.count():
            x = QA_RECORDS_PER_DOCUMENT - flagged
            unflagged = list(
                elps.filter(extractedlistpresence__qa_flag=False)
                .order_by("?")  # this makes the selection random
                .values_list("pk", flat=True)
            )
            lps = ExtractedListPresence.objects.filter(pk__in=unflagged[:x])
            for lp in lps:
                lp.qa_flag = True
                lp.save()
            other_lps = ExtractedListPresence.objects.filter(pk__in=unflagged[x:])
        if flagged >= QA_RECORDS_PER_DOCUMENT:
            # we need to unflag those over a count of 30 so they won't show
            for lp in elps.filter(extractedlistpresence__qa_flag=True)[
                QA_RECORDS_PER_DOCUMENT:
            ]:
                lp.qa_flag = False
                lp.save()
            other_lps = elps.filter(extractedlistpresence__qa_flag=False)

        return (
            self.rawchem.select_subclasses().filter(
                extractedlistpresence__qa_flag=True
            ),
            other_lps,
        )

    def mark_other_lps(self, lps):
        if lps:
            for lp in lps:
                lp.qa_flag = True
                lp.save()
