import re
from django.db.models import (
    Case,
    Count,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)

from django.http import JsonResponse
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.html import format_html
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django_datatables_view.base_datatable_view import BaseDatatableView
from dashboard.models import (
    AuditLog,
    DataDocument,
    DSSToxLookup,
    ExtractedCPCat,
    ExtractedHabitsAndPractices,
    ExtractedListPresenceTag,
    FunctionalUseToRawChem,
    GroupType,
    Product,
    ProductToPUC,
    RawChem,
)
from dashboard.utils import GroupConcat, parse_ordering
from lib.cache import cache_page
from mmdb.models import MediaSampleSummary


class FilterDatatableView(BaseDatatableView):
    def get_filter_method(self):
        return self.FILTER_ICONTAINS


class PucFunctionalUseListJson(BaseDatatableView):
    """
    Provides JSON elements describing each functional use that appears in each
    document associated via Product to the detail page's PUC as the uberpuc.
    """

    model = FunctionalUseToRawChem
    columns = [
        "chemical.extracted_text.data_document.data_group.group_type.title",
        "chemical.extracted_text.data_document.title",  # DataDocument title with link to detail page
        "preferred_name",  # Preferred chemical name
        "preferred_cas",  # Preferred CAS
        "functional_use.report_funcuse",  # Reported Functional Use
        "functional_use.category.title",  # Harmonized Functional Use
    ]

    def get_initial_queryset(self):
        qs = (
            super()
            .get_initial_queryset()
            .annotate(
                preferred_name=Case(
                    # no dsstox
                    When(
                        chemical__dsstox__isnull=False,
                        then=F("chemical__dsstox__true_chemname"),
                    ),
                    # not blank raw_chem_name
                    When(
                        ~Q(chemical__raw_chem_name=""),
                        then=F("chemical__raw_chem_name"),
                    ),
                    # no true chem no raw_chem_name
                    default=Value("Unnamed Chemical"),
                ),
                preferred_cas=Case(
                    # no dsstox
                    When(
                        chemical__dsstox__isnull=False,
                        then=F("chemical__dsstox__true_cas"),
                    ),
                    # not blank raw_chem_name
                    When(~Q(chemical__raw_chem_name=""), then=F("chemical__raw_cas")),
                    # no true chem no raw_chem_name
                    default=Value(""),
                ),
            )
            .select_related(
                "functional_use__category",
                "chemical__extracted_text__data_document",
                "chemical__dsstox",
                "chemical__dsstox",
            )
        )
        puc_id = self.request.GET.get("puc")

        if puc_id:
            return qs.filter(
                Q(
                    chemical__extracted_text__data_document__product__product_uber_puc__puc_id=puc_id
                )
            ).distinct()
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "chemical.extracted_text.data_document.title":
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                row.chemical.extracted_text.data_document.get_absolute_url(),
                value,
            )
        elif column == "functional_use.category.title":
            if row.functional_use.category != None:
                return format_html(
                    '<a href="{}" title="Go to function detail" target="_blank">{}</a>',
                    row.functional_use.category.get_absolute_url(),
                    value,
                )
        return value


class ProductListJson(FilterDatatableView):
    """
    Provides JSON elements describing each Product related to
    the detail page's PUC as the uberpuc.
    """

    model = Product
    columns = [
        "title",
        "brand_name",
        "manufacturer",
        "product_uber_puc.classification_method.name",
    ]

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "title":
            return format_html(
                '<a href="{}" title="Go to Product detail" target="_blank">{}</a>',
                row.get_absolute_url(),
                value,
            )
        if column == "product_uber_puc.classification_method.name":
            if value:
                return format_html(
                    '<span title="{}">{}</span>',
                    row.product_uber_puc.classification_method.description,
                    value,
                )
        return value

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        puc = self.request.GET.get("puc")
        if puc:
            return qs.filter(Q(product_uber_puc__puc=puc))
        return qs

    def ordering(self, qs):
        """Get parameters from the request and prepare order by clause"""

        order = parse_ordering(self, qs)
        if order:
            order_column = order[0]

            if order_column.endswith("classification_method__name"):
                reverse_order = order_column.startswith("-")
                if reverse_order:
                    return qs.order_by(
                        F("product_uber_puc__classification_method__rank").desc(
                            nulls_last=True
                        )
                    )
                else:
                    return qs.order_by(
                        F("product_uber_puc__classification_method__rank").asc(
                            nulls_last=True
                        )
                    )
            else:
                return qs.order_by(*order)
        return qs


class DocumentListJson(FilterDatatableView):
    """
    Provides JSON elements describing each document with products assigned
    to the page's PUC as uberpuc
    """

    model = DataDocument
    columns = [
        "title",
        "data_group.group_type.title",
        "extractedtext.doc_date",
        "extractedtext.rawchem.raw_chem_name",
        "extractedtext.rawchem.raw_cas",
    ]

    document_rslt = {}

    def create_rawchem_document_map(self, sid):
        if sid and (len(DocumentListJson.document_rslt) == 0):
            rawchems = RawChem.objects.filter(Q(dsstox__sid=sid)).values(
                "extracted_text", "raw_cas", "raw_chem_name"
            )
            for rawchem in rawchems:
                DocumentListJson.document_rslt[rawchem["extracted_text"]] = rawchem

    def get_initial_queryset(self):
        puc = self.request.GET.get("puc")
        sid = self.request.GET.get("sid")
        if puc:
            return qs.filter(Q(products__product_uber_puc__puc=puc)).distinct()
        self.create_rawchem_document_map(sid)
        qs = super().get_initial_queryset()
        if sid:
            return qs.filter(Q(extractedtext__rawchem__dsstox__sid=sid)).distinct()
        return qs

    def render_column(self, row, column):
        sid = self.request.GET.get("sid")
        if column == "extractedtext.rawchem.raw_chem_name":
            if not sid or row.id not in DocumentListJson.document_rslt:
                return None
            return DocumentListJson.document_rslt[row.id]["raw_chem_name"]
        if column == "extractedtext.rawchem.raw_cas":
            if not sid or row.id not in DocumentListJson.document_rslt:
                return None
            return DocumentListJson.document_rslt[row.id]["raw_cas"]
        if column == "extractedtext.doc_date":
            if hasattr(row, "extractedtext"):
                value = row.extractedtext.doc_date
                return value
            else:
                value = None
                return value
        value = self._render_column(row, column)
        chem = self.request.GET.get("chem_detail")
        if column == "title":
            if chem:
                value = truncatechars(value, 50)
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                row.get_absolute_url(),
                value,
            )
        if column == "data_group.group_type.title":
            return format_html(
                '<span title="{}">{}</span>',
                row.data_group.group_type.description,
                value,
            )
        return value

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        puc = self.request.GET.get("category")
        pid = self.request.GET.get("pid")
        group_type = self.request.GET.get("group_type")
        if puc:
            qs = qs.filter(Q(products__product_uber_puc__puc=puc))
        if group_type:
            if group_type != "-1":
                qs = qs.filter(data_group__group_type__id=group_type)
        if pid:
            included_ids = list(
                map(int, self.request.GET.get("included_ids").split(","))
            )
            qs = qs.filter(pk__in=included_ids)
        return qs


class ChemicalListJson(FilterDatatableView):
    """
    Provides JSON elements describing each curated chemical that is
    associated via Product to the detail page's PUC as the uberpuc.
    """

    model = DSSToxLookup
    columns = ["sid", "true_cas", "true_chemname", "raw_count_ma", "raw_count_au"]

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        puc = self.request.GET.get("puc")
        if puc:
            qs = qs.filter(
                curated_chemical__extracted_text__data_document__product__product_uber_puc__puc=puc
            ).annotate(raw_count=Count("curated_chemical"))

            sids_au_counts = []
            sids_ma_counts = []

            qs_ma = (
                super()
                .get_initial_queryset()
                .filter(
                    Q(
                        curated_chemical__extracted_text__data_document__product__product_uber_puc__puc=puc
                    )
                    & Q(
                        curated_chemical__extracted_text__data_document__product__product_uber_puc__classification_method__code__in=(
                            "MA",
                            "AC",
                            "MB",
                            "BA",
                        )
                    )
                )
                .annotate(raw_count_ma=Count("curated_chemical"))
            )

            for elem in qs_ma:
                sids_ma_counts.append(When(sid=elem.sid, then=Value(elem.raw_count_ma)))

            qs_au = (
                super()
                .get_initial_queryset()
                .filter(
                    Q(
                        curated_chemical__extracted_text__data_document__product__product_uber_puc__puc=puc
                    )
                    & Q(
                        curated_chemical__extracted_text__data_document__product__product_uber_puc__classification_method__code="AU"
                    )
                )
                .annotate(raw_count_au=Count("curated_chemical"))
            )

            for elem in qs_au:
                sids_au_counts.append(When(sid=elem.sid, then=Value(elem.raw_count_au)))

            qs = qs.annotate(
                raw_count_ma=Case(
                    *sids_ma_counts, default=0, output_field=IntegerField()
                )
            ).annotate(
                raw_count_au=Case(
                    *sids_au_counts, default=0, output_field=IntegerField()
                )
            )

        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if value and hasattr(row, "get_absolute_url"):
            if column == "true_chemname":
                return format_html(truncatechars(value, 89))
            if column == "raw_count_au" or column == "raw_count_ma":
                return value
            return format_html(
                '<a href="{}" title="Go to Chemical detail" target="_blank">{}</a>',
                row.get_absolute_url(),
                value,
            )
        return value

    def filter_queryset(self, qs):
        s = self.request.GET.get("search[value]", None)
        if s:
            qs = qs.filter(
                Q(true_cas__icontains=s)
                | Q(true_chemname__icontains=s)
                | Q(sid__icontains=s)
            ).distinct()
        return qs


class ListPresenceTagSetsJson(SingleObjectMixin, View):
    """
    Provides JSON elements describing each distinct combination of tags
    that a tag appears in.
    """

    model = ExtractedListPresenceTag

    def get(self, request, *args, **kwargs):
        tagsets = self.get_object().get_tagsets()
        tagsets_list = []
        for tagset in tagsets:
            tagset_names = []
            for tag in sorted(tagset, key=lambda o: o.name.lower()):
                tagset_names.append(
                    f"<a href='{reverse('lp_tag_detail', args=[tag.id])}' title='{tag.definition or 'No Definition'}'>{tag.name}</a>"
                )
            tagsets_list.append([" ; ".join(tagset_names)])
        return JsonResponse({"data": sorted(tagsets_list)}, safe=False)


class ListPresenceChemicalJson(BaseDatatableView):
    model = ExtractedListPresenceTag
    columns = ["sid", "true_cas", "true_chemname"]

    def get_initial_queryset(self):
        obj = ExtractedListPresenceTag.objects.get(pk=self.kwargs["pk"])
        tagsets = obj.get_tagsets()
        chems = obj.get_dsstox(tagsets)
        return chems

    def render_column(self, row, column):
        if column == "sid":
            return f"<a href='{reverse('chemical', args=[row.sid])}' title={row.sid}'>{row.sid}</a>"
        if column == "true_cas":
            return f"{row.true_cas}"
        if column == "true_chemname":
            return f"{row.true_chemname}"
        return super().render_column(row, column)

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        tagnb = self.request.GET.get("presence_tag")
        if tagnb:
            obj = ExtractedListPresenceTag.objects.get(pk=self.kwargs["pk"])
            tagsets = obj.get_tagsets()
            qs &= obj.get_dsstox([tagsets[int(tagnb)]])
        return qs


class ListPresenceDocumentsJson(BaseDatatableView):
    """
    This view returns all the ExtractedCPCat documents where at least one
    ExtractedListPresence child record has been associated with the list
    presence tag identified by the "tag_pk" id argument.
    Along with each ExtractedCPCat record, it returns the unique tags related
    to that document's child records.
    """

    model = ExtractedCPCat
    columns = ["data_document.title", "tags"]

    def get_filter_method(self):
        return self.FILTER_ICONTAINS

    def get_initial_queryset(self):
        qs = self.model.objects.filter(
            rawchem__extractedlistpresence__tags__pk=self.kwargs["tag_pk"]
        ).distinct()
        return qs

    def render_column(self, row, column):
        if column == "data_document.title":
            return f"<a href='{reverse('data_document', args=[row.data_document.id])}' title={row}'>{row}</a>"
        if column == "tags":
            tag_str_list = []
            tags = (
                ExtractedListPresenceTag.objects.filter(
                    extractedlistpresence__extracted_text__data_document=row.data_document_id
                )
                .order_by("name")
                .distinct()
            )
            for tag in tags:
                tag_str_list.append(
                    f"<a href='{reverse('lp_tag_detail', args=[tag.id])}' title='{tag.definition or 'No Definition'}'>{tag.name.lower()}</a>"
                )
            return " ; ".join(tag_str_list)
        return super().render_column(row, column)

    def filter_queryset(self, qs):
        qs_django_filtered = super().filter_queryset(qs)
        search = self._querydict.get("search[value]", None)
        pid = self.request.GET.get("presence_tag")
        if pid:
            included_pids = list(
                map(int, self.request.GET.get("all_presence_tags").split(","))
            )
            qs = qs.filter(pk__in=included_pids)
            qs_django_filtered = qs_django_filtered.filter(pk__in=included_pids)

        if search:
            # dealing with column can't search on out of the box (tag column)
            filteredtags = []
            for e in qs:
                tags = (
                    ExtractedListPresenceTag.objects.filter(
                        extractedlistpresence__extracted_text__data_document=e.data_document_id
                    )
                    .order_by("name")
                    .distinct()
                )
                for tag in tags:
                    if search.lower() in re.split(r"[, :-_\\//]", tag.name.lower()):
                        filteredtags.append(e.data_document_id)
                        break
            qs = qs.filter(data_document_id__in=filteredtags)

        return qs | qs_django_filtered


class FUCProductListJson(FilterDatatableView):
    model = Product
    columns = [
        "title",
        "document.title",
        "product_uber_puc.puc",
        "product_uber_puc.classification_method.name",
    ]

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "title":
            return format_html(
                '<a href="{}" title="Go to Product detail" target="_blank">{}</a>',
                row.get_absolute_url(),
                value,
            )
        if column == "document.title":
            return format_html(
                '<a href="{}" title="Go to Data Document detail" target="_blank">{}</a>',
                row.document.get_absolute_url(),
                value,
            )
        if column == "product_uber_puc.puc":
            if value:
                return format_html(
                    '<a href="{}" title="Go to PUC detail" target="_blank">{}</a>',
                    row.product_uber_puc.puc.get_absolute_url(),
                    value,
                )
        if column == "product_uber_puc.classification_method.name":
            if value:
                return format_html(
                    '<span title="{}">{}</span>',
                    row.product_uber_puc.classification_method.description,
                    value,
                )
        return value

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        fuc = self.request.GET.get("functional_use_category")
        qs = qs.select_related("product_uber_puc")
        if fuc:
            return qs.filter(
                Q(datadocument__extractedtext__rawchem__functional_uses__category=fuc)
            ).distinct()
        return qs

    def ordering(self, qs):
        """Get parameters from the request and prepare order by clause"""

        order = parse_ordering(self, qs)
        if order:
            order_column = order[0]
            if order_column.endswith("classification_method__name"):
                reverse_order = order_column.startswith("-")
                if reverse_order:
                    return qs.order_by(
                        F("product_uber_puc__classification_method__rank").desc(
                            nulls_last=True
                        )
                    )
                else:
                    return qs.order_by(
                        F("product_uber_puc__classification_method__rank").asc(
                            nulls_last=True
                        )
                    )
            else:
                return qs.order_by(*order)
        return qs


class FUCDocumentListJson(FilterDatatableView):
    model = RawChem
    columns = [
        "extracted_text__data_document__data_group__group_type__title",
        "extracted_text__data_document__title",
        "extracted_text__doc_date",
        "functional_uses__report_funcuse",
    ]

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        fuc = self.request.GET.get("functional_use_category")
        if fuc:
            qs = qs.filter(Q(functional_uses__category=fuc))
        # using the .distinct() function means that a dict is returned, not
        # a queryset.
        qs = (
            qs.order_by(
                "extracted_text__data_document__data_group__group_type__title",
                "extracted_text__data_document__title",
            )
            .values(
                "extracted_text__data_document",
                "extracted_text__data_document__title",
                "extracted_text__data_document__data_group__group_type__title",
                "extracted_text__data_document__data_group__group_type__description",
                "extracted_text__doc_date",
                "functional_uses__report_funcuse",
            )
            .distinct()
        )
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "extracted_text__data_document__title":
            doc_id = row["extracted_text__data_document"]
            doc = DataDocument.objects.get(pk=doc_id)
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                doc.get_absolute_url(),
                value,
            )
        if column == "extracted_text__data_document__data_group__group_type__title":
            return format_html(
                '<span title="{}">{}</span>',
                row[
                    "extracted_text__data_document__data_group__group_type__description"
                ],
                value,
            )
        return value


class FUCChemicalListJson(FilterDatatableView):
    model = DSSToxLookup
    columns = ["sid", "true_cas", "true_chemname"]

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        fuc = self.request.GET.get("functional_use_category")
        if fuc:
            vals = (
                RawChem.objects.filter(dsstox__isnull=False)
                .filter(Q(functional_uses__category=fuc))
                .values("dsstox")
            )
            return qs.filter(pk__in=vals)
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if value and hasattr(row, "get_absolute_url"):
            if column == "true_chemname":
                return format_html(truncatechars(value, 89))
            return format_html(
                '<a href="{}" title="Go to Chemical detail" target="_blank">{}</a>',
                row.get_absolute_url(),
                value,
            )
        return value

    def filter_queryset(self, qs):
        s = self.request.GET.get("search[value]", None)
        if s:
            qs = qs.filter(
                Q(true_cas__icontains=s)
                | Q(true_chemname__icontains=s)
                | Q(sid__icontains=s)
            ).distinct()
        return qs


class HarmonizedMediumDocumentListJson(FilterDatatableView):
    model = DataDocument
    columns = [
        "data_group__group_type__code",
        "title",
        "extractedtext__doc_date",
        "extractedtext__rawchem__unionextractedlmhhrec__medium",
    ]

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        medium = self.request.GET.get("medium")
        if medium:
            qs = qs.filter(
                Q(
                    extractedtext__rawchem__unionextractedlmhhrec__harmonized_medium=medium
                )
            )
        # using the .distinct() function means that a dict is returned, not
        # a queryset.
        qs = (
            qs.order_by("data_group__group_type__code", "title")
            .values(
                "id",
                "title",
                "data_group__group_type__code",
                "extractedtext__doc_date",
                "extractedtext__rawchem__unionextractedlmhhrec__medium",
            )
            .distinct()
        )
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "title":
            doc_id = row["id"]
            doc = DataDocument.objects.get(pk=doc_id)
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                doc.get_absolute_url(),
                value,
            )
        return value


class HarmonizedMediumChemicalListJson(FilterDatatableView):
    """
    This display includes DTXSID records from both curated Factotum
    chemicals,
    """

    model = DSSToxLookup
    columns = ["sid", "true_chemname", "true_cas"]

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        medium = self.request.GET.get("medium")
        if medium:
            factotum_chems = (
                RawChem.objects.filter(dsstox__isnull=False)
                .filter(Q(unionextractedlmhhrec__harmonized_medium=medium))
                .values_list("dsstox__id", flat=True)
            )
            mmdb_chems = (
                MediaSampleSummary.objects.filter(dsstox__isnull=False)
                .filter(Q(harmonized_medium=medium))
                .values_list("dsstox__id", flat=True)
            )
            vals = list(factotum_chems) + list(mmdb_chems)
            return qs.filter(id__in=vals)
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if value and hasattr(row, "get_absolute_url"):
            if column == "true_chemname":
                return format_html(truncatechars(value, 89))
            return format_html(
                '<a href="{}" title="Go to Chemical detail" target="_blank">{}</a>',
                row.get_absolute_url(),
                value,
            )
        return value

    def filter_queryset(self, qs):
        s = self.request.GET.get("search[value]", None)
        if s:
            qs = qs.filter(
                Q(true_cas__icontains=s)
                | Q(true_chemname__icontains=s)
                | Q(sid__icontains=s)
            ).distinct()
        return qs


class HarmonizedMediumSampleSummaryListJson(FilterDatatableView):
    model = MediaSampleSummary
    columns = [
        "source_name",
        "data_type",
        "reported_medium",
        "reported_species",
        "dsstox.true_chemname",
        "dsstox.true_cas",
        "number_of_observations",
        "detected_sample_count",
        "chem_detected_flag",
    ]

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        medium = self.request.GET.get("medium")
        if medium:
            return qs.filter(harmonized_medium_id=medium)
        return qs

    def filter_queryset(self, qs):
        """
        This breaks when the charsets are inconsistent
        """
        s = self.request.GET.get("search[value]", None)
        if s:
            qs = qs.filter(
                Q(source_name__icontains=s)
                | Q(reported_species__icontains=s)
                | Q(dsstox__true_chemname__icontains=s)
            ).distinct()
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "dsstox.true_chemname":
            return format_html(
                '<a href="{}" title="Go to Chemical detail" target="_blank">{}</a>',
                row.dsstox.get_absolute_url(),
                value,
            )
        if column == "chem_detected_flag":
            return row.get_chem_detected_flag_display()
        return value


class ChemicalSampleSummaryListJson(FilterDatatableView):
    model = MediaSampleSummary
    columns = [
        "source_name",
        "data_type",
        "harmonized_medium",
        "reported_medium",
        "reported_species",
        "number_of_observations",
        "detected_sample_count",
        "chem_detected_flag",
    ]

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        sid = self.request.GET.get("sid")
        if sid:
            return qs.filter(dsstox=sid)
        return qs

    def filter_queryset(self, qs):
        """
        This breaks when the charsets are inconsistent
        """
        s = self.request.GET.get("search[value]", None)
        if s:
            qs = qs.filter(
                Q(source_name__icontains=s)
                | Q(reported_species__icontains=s)
                | Q(dsstox__true_chemname__icontains=s)
            ).distinct()
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "harmonized_medium" and row.harmonized_medium is not None:
            return format_html(
                '<a href="{}" title="Go to Harmonized Medium detail" target="_blank">{}</a>',
                row.harmonized_medium.get_absolute_url(),
                value,
            )
        if column == "chem_detected_flag":
            return row.get_chem_detected_flag_display()
        return value


@cache_page(86400)
def sids_by_grouptype_ajax(request):
    """Counts the number of DTXSIDs per GroupType. Multiple
    GroupTypes can be associated with a single DTXSID. The
    GroupType set is also counted.
    The output is a JSON to be rendered with this library
    https://github.com/benfred/venn.js
    Args:
        request ([type]): [description]
    """
    qs = DSSToxLookup.objects.annotate(
        grouptype=GroupConcat(
            "curated_chemical__extracted_text__data_document__data_group__group_type__id",
            distinct=True,
        )
    ).values_list("grouptype", flat=True)
    sets_cnt = {}

    def add_set(key):
        # Adds or creates set to sets_dict
        if key not in sets_cnt:
            sets_cnt[key] = 1
        else:
            sets_cnt[key] += 1

    # Count sets
    for group_str in qs:
        # Ignore "None"
        if group_str:
            # Each value is a concatenation of GroupType IDs separated by a comma.
            # Lets split them
            groups = group_str.split(",")
            # Then turn them into a list of integers
            groups = [int(i) for i in groups]
            # We want to make sure they are consistently sorted
            groups.sort()
            # We make them a tuple to use as a dictionary key
            groups = tuple(groups)
            # Record a count on it
            add_set(groups)
            # If this is more than one GroupType, we also want to count the GroupTypes
            # within the set
            if len(groups) > 1:
                for group in groups:
                    add_set((group,))

    # Here is a dictionary relating the GroupType ID we've counted on to its title
    titles = {
        g["id"]: g["title"]
        for g in GroupType.objects.all().order_by("id").values("id", "title")
    }
    # Create data
    sets = []
    for set_ids, set_cnt in sets_cnt.items():
        # List the titles, not IDs
        set_groups = [titles[i] for i in set_ids]
        # Make the final dictionary output
        sets.append({"sets": set_groups, "size": set_cnt})

    return JsonResponse({"data": sets})


class ProductPUCReconciliationJson(FilterDatatableView):
    """
    Provides JSON elements describing all Products where more
    than one PUC has been assigned
    """

    model = ProductToPUC
    columns = [
        "product_id",
        "product__title",
        "puc",
        "classification_method",
        "classification_confidence",
    ]

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "product__title":
            return format_html(
                '<a href="{}" title="Go to Product detail" target="_blank">{}</a>',
                row.product.get_absolute_url(),
                row.product.title,
            )
        if column == "puc":
            return format_html(
                '<a href="{}" title="Go to PUC detail" target="_blank">{}</a>',
                row.puc.get_absolute_url(),
                value,
            )
        # if column == "unassign":
        #     return format_html(
        #         '<a href="unassign?puc={}&product={}" title="Remove assignment" target="_blank">Unassign</a>',
        #         row.puc_id,
        #         row.product_id,
        #     )
        return value

    def get_initial_queryset(self):
        dupes = (
            ProductToPUC.objects.values("product_id")
            .annotate(puc_count=Count("puc_id", distinct=True))
            .filter(puc_count__gte=2)
        )
        qs = ProductToPUC.objects.filter(
            product_id__in=Subquery(dupes.values("product_id"))
        ).order_by("product_id")
        return qs


class HabitsAndPracticesDocumentsJson(FilterDatatableView):
    model = ExtractedHabitsAndPractices
    columns = [
        "extracted_text.data_document.title",
        "product_surveyed",
        "data_type.title",
    ]

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        puc = self.request.GET.get("puc")
        if puc:
            return qs.filter(Q(puc=puc))
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "extracted_text.data_document.title":
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                row.extracted_text.data_document.get_absolute_url()
                + "#chem-card-"
                + str(row.pk),
                value,
            )
        return value


class CuratedChemicalDetailJson(FilterDatatableView):
    model = RawChem
    columns = ["extracted_text.data_document.title", "sid_updated", "provisional"]

    def get_initial_queryset(self):
        sid = self.request.GET.get("sid")
        raw_chem_name = self.request.GET.get("raw_chem_name")
        raw_cas = self.request.GET.get("raw_cas")

        sid_log = (
            AuditLog.objects.filter(rawchem_id=OuterRef("pk"), field_name="sid")
            .order_by("-date_created")
            .values("date_created")
        )

        qs = (
            super()
            .get_initial_queryset()
            .prefetch_related("extracted_text__data_document", "dsstox")
            .filter(dsstox__sid=sid, raw_chem_name=raw_chem_name, raw_cas=raw_cas)
            .annotate(sid_updated=Subquery(sid_log[:1]))
        )
        return qs

    def render_column(self, row, column):
        if column == "extracted_text.data_document.title":
            dd_url = reverse(
                "data_document", args=[row.extracted_text.data_document.id]
            )
            dd_url += f"#chem-card-{row.id}"
            return f"<a href='{dd_url}' target='_blank'>{row.extracted_text.data_document.title}</a>"
        elif column == "sid_updated":
            return (
                row.sid_updated.strftime("%b %d, %Y, %I:%M:%S %p")
                if row.sid_updated
                else ""
            )
        elif column == "provisional":
            return "Yes" if row.provisional else "No"
        return super().render_column(row, column)

    def filter_queryset(self, qs):
        pv = self.request.GET.get("provisional")
        if pv and pv != "all":
            qs = qs.filter(provisional=pv)
        return super().filter_queryset(qs)
