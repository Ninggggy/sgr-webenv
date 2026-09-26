from django.contrib.auth.decorators import login_required
from django.db.models import Q, F, When, Case, Value, CharField
from django.shortcuts import render, get_object_or_404
from django.utils.html import format_html
from django_datatables_view.base_datatable_view import BaseDatatableView

from factotum.app_type import select_template_for_app


from dashboard.models import (
    DataDocument,
    DSSToxLookup,
    PUC,
    ProductDocument,
    PUCKind,
    RawChem,
    DuplicateChemicals,
    ProductToPucClassificationMethod,
    ExtractedComposition,
    FunctionalUseToRawChem,
    UnionExtractedLMHHRec,
)
from dashboard.utils import (
    get_download_filename,
    render_to_csv_response,
    parse_ordering,
)


def chemical_detail(request, sid, puc_id=None):
    chemical = get_object_or_404(DSSToxLookup, sid=sid)
    puc = get_object_or_404(PUC, id=puc_id) if puc_id else None
    keysets = chemical.get_tag_sets()
    group_types = chemical.get_unique_datadocument_group_types_for_dropdown()
    puc_kinds = PUCKind.objects.all()
    classification_methods = ProductToPucClassificationMethod.objects.all()
    is_co_chem = group_types.filter(code="CO").count() > 0

    formulation_pucs = chemical.get_cumulative_puc_products_tree("FO")
    article_pucs = chemical.get_cumulative_puc_products_tree("AR")
    occupation_pucs = chemical.get_cumulative_puc_products_tree("OC")

    context = {
        "chemical": chemical,
        "keysets": keysets,
        "group_types": group_types,
        "formulation_pucs": formulation_pucs,
        "article_pucs": article_pucs,
        "occupation_pucs": occupation_pucs,
        "puc": puc,
        "show_filter": True,
        "puc_kinds": puc_kinds,
        "classification_methods": classification_methods,
        "is_co_chem": is_co_chem,
    }

    template_name = select_template_for_app(
        internal="chemicals/chemical_detail_internal.html",
        external="chemicals/chemical_detail.html",
    )

    return render(request, template_name, context)


def download_documents_chemical(request, sid):
    data = {}
    data["chem_name"] = []
    data["CAS"] = []

    rawchems = RawChem.objects.filter(dsstox__sid=sid)
    for rawchem in rawchems:
        data["chem_name"].append(
            When(
                pk=rawchem.extracted_text.data_document.id,
                then=Value(rawchem.raw_chem_name),
            )
        )
        data["CAS"].append(
            When(
                pk=rawchem.extracted_text.data_document.id, then=Value(rawchem.raw_cas)
            )
        )

    documents = (
        DataDocument.objects.filter(extractedtext__rawchem__dsstox__sid=sid)
        .values(
            "title",
            "extractedtext__data_document__data_group__group_type__title",
            "extractedtext__doc_date",
        )
        .annotate(
            chem_name=Case(*data["chem_name"], default=0, output_field=CharField()),
            CAS=Case(*data["CAS"], default=0, output_field=CharField()),
        )
        .order_by("title")
        .distinct()
    )
    filename = get_download_filename(f"{sid}_documents", "csv")
    return render_to_csv_response(
        documents,
        filename=filename,
        field_header_map={
            "title": "Data Document Title",
            "extractedtext__data_document__data_group__group_type__title": "Data Type",
            "extractedtext__doc_date": "Document Date",
            "chem_name": "Reported Chemical name",
            "CAS": "Reported CAS",
        },
    )


def download_composition_chemical(request, sid):
    chems = (
        ExtractedComposition.objects.filter(dsstox__sid=sid)
        .prefetch_related(
            "weight_fraction_type",
            "unit_type",
            "extracted_text__data_document__products__product_uber_puc__puc",
        )
        .values(
            "extracted_text__data_document__id",
            "extracted_text__data_document__title",
            "extracted_text__doc_date",
            "extracted_text__data_document__products__title",
            "extracted_text__data_document__products__product_uber_puc__puc__gen_cat",
            "extracted_text__data_document__products__product_uber_puc__puc__prod_fam",
            "extracted_text__data_document__products__product_uber_puc__puc__prod_type",
            "extracted_text__data_document__products__product_uber_puc__classification_method__name",
            "extracted_text__data_document__products__tags_name",
            "raw_min_comp",
            "raw_max_comp",
            "raw_central_comp",
            "unit_type__title",
            "lower_wf_analysis",
            "upper_wf_analysis",
            "central_wf_analysis",
            "weight_fraction_type__title",
            "component",
        )
        .order_by(
            "extracted_text__data_document__title",
            "extracted_text__data_document__products__title",
            "rawchem_ptr_id",
        )
    )
    filename = get_download_filename(f"{sid}_products_and_weight_fractions", "csv")
    return render_to_csv_response(
        chems,
        filename=filename,
        use_verbose_names=False,
        field_header_map={
            "extracted_text__data_document__id": "Data Document ID",
            "extracted_text__data_document__title": "Data Document Title",
            "extracted_text__doc_date": "Document Date",
            "extracted_text__data_document__products__title": "Product Name",
            "extracted_text__data_document__products__product_uber_puc__puc__gen_cat": "PUC General Category",
            "extracted_text__data_document__products__product_uber_puc__puc__prod_fam": "PUC Product Family",
            "extracted_text__data_document__products__product_uber_puc__puc__prod_type": "PUC Product Type",
            "extracted_text__data_document__products__product_uber_puc__classification_method__name": "PUC Classification Method",
            "extracted_text__data_document__products__tags_name": "Attributes",
            "raw_min_comp": "Raw Min Comp",
            "raw_max_comp": "Raw Max Comp",
            "raw_central_comp": "Raw Central Comp",
            "unit_type__title": "Unit Type",
            "lower_wf_analysis": "Lower Weight Fraction",
            "upper_wf_analysis": "Upper Weight Fraction",
            "central_wf_analysis": "Central Weight Fraction",
            "weight_fraction_type__title": "Weight Fraction Type",
            "component": "Component",
        },
    )


def download_functional_uses_chemical(request, sid):
    functional_uses = (
        FunctionalUseToRawChem.objects.filter(chemical__dsstox__sid=sid)
        .select_related(
            "functional_use__category",
            "chemical__extracted_text__data_document__data_group__group_type",
        )
        .values(
            "chemical__extracted_text__data_document__data_group__group_type__title",
            "chemical__extracted_text__data_document__id",
            "chemical__extracted_text__data_document__title",
            "chemical__extracted_text__doc_date",
            "functional_use__report_funcuse",
            "functional_use__category__title",
        )
        .order_by(
            "chemical__extracted_text__data_document__data_group__group_type__title"
        )
    )
    filename = get_download_filename(f"{sid}_functional_uses", "csv")
    return render_to_csv_response(
        functional_uses,
        filename=filename,
        use_verbose_names=False,
        field_header_map={
            "chemical__extracted_text__data_document__data_group__group_type__title": "Data Type",
            "chemical__extracted_text__data_document__id": "Data Document ID",
            "chemical__extracted_text__data_document__title": "Data Document Title",
            "chemical__extracted_text__doc_date": "Document Date",
            "functional_use__report_funcuse": "Reported Function",
            "functional_use__category__title": "Harmonized Function",
        },
    )


@login_required()
def duplicate_chemical_records(
    request, template_name="chemicals/duplicate_chemicals.html"
):
    data = {"chemicals": {}}
    return render(request, template_name, data)


class DuplicateChemicalsJson(BaseDatatableView):
    model = RawChem
    columns = ["extracted_text__data_document__title", "dsstox__sid"]

    def get_filter_method(self):
        return self.FILTER_ICONTAINS

    def get_initial_queryset(self):
        qs = (
            DuplicateChemicals.objects.filter(
                extracted_text__data_document__data_group__group_type__code="CO"
            )
        ).values(
            "extracted_text__data_document",
            "extracted_text__data_document__title",
            "dsstox__sid",
        )
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)

        if column == "extracted_text__data_document__title":
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                "/datadocument/{}/".format(row["extracted_text__data_document"]),
                value,
            )
        return value


class ChemicalProductListJson(BaseDatatableView):
    model = ProductDocument
    columns = [
        "product.title",
        "product.manufacturer",
        "product.brand_name",
        "document.title",
        "product.product_uber_puc.puc",
        "product.product_uber_puc.puc.kind.name",
        "product.product_uber_puc.classification_method.name",
    ]

    def get_filter_method(self):
        return self.FILTER_ICONTAINS

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        sid = self.request.GET.get("sid")
        if sid:
            return qs.filter(
                Q(document__extractedtext__rawchem__dsstox__sid=sid)
            ).distinct()
        return qs.filter()

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "product.title":
            return format_html(
                '<a href="{}" title="Go to Product detail" target="_blank">{}</a>',
                row.product.get_absolute_url(),
                value,
            )
        if column == "document.title":
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                row.document.get_absolute_url(),
                value,
            )
        if column == "product.product_uber_puc.puc":
            if value:
                return format_html(
                    '<a href="{}" title="Go to PUC detail" target="_blank">{}</a>',
                    row.product.product_uber_puc.puc.get_absolute_url(),
                    value,
                )
        if column == "product.product_uber_puc.puc.kind.name":
            if value:
                return format_html(
                    '<span title="{}">{}</span>',
                    row.product.product_uber_puc.puc.kind.description,
                    value,
                )
        if column == "product.product_uber_puc.classification_method.name":
            if value:
                return format_html(
                    '<span title="{}">{}</span>',
                    row.product.product_uber_puc.classification_method.description,
                    value,
                )

        return value

    def ordering(self, qs):
        """Get parameters from the request and prepare order by clause"""

        order = parse_ordering(self, qs)

        if order:
            order_column = order[0]
            if order_column.endswith("product_uber_puc__puc"):
                # sort PUC data with nulls at bottom
                reverse_order = order_column.startswith("-")
                if reverse_order:
                    qs = qs.order_by(
                        F("product__product_uber_puc__puc__gen_cat").desc(
                            nulls_last=True
                        ),
                        *order,
                    )
                else:
                    qs = qs.order_by(
                        F("product__product_uber_puc__puc__gen_cat").asc(
                            nulls_last=True
                        ),
                        *order,
                    )
                return qs
            elif order_column.endswith("puc__kind__name"):
                # sort PUC data with nulls at bottom
                reverse_order = order_column.startswith("-")
                if reverse_order:
                    qs = qs.order_by(
                        F("product__product_uber_puc__puc__kind__name").desc(
                            nulls_last=True
                        )
                    )
                else:
                    qs = qs.order_by(
                        F("product__product_uber_puc__puc__kind__name").asc(
                            nulls_last=True
                        )
                    )
            elif order_column.endswith("classification_method__name"):
                reverse_order = order_column.startswith("-")
                if reverse_order:
                    return qs.order_by(
                        F(
                            "product__product_uber_puc__classification_method__rank"
                        ).desc(nulls_last=True)
                    )
                else:
                    return qs.order_by(
                        F("product__product_uber_puc__classification_method__rank").asc(
                            nulls_last=True
                        )
                    )
            else:
                return qs.order_by(*order)
        return qs

    def filter_queryset(self, qs):
        puc = self.request.GET.get("category")
        s = self.request.GET.get("search[value]", None)
        puc_kind = self.request.GET.get("puc_kind")
        cm = self.request.GET.get("cm")
        if puc:
            qs = qs.filter(Q(product__product_uber_puc__puc_id=puc))
        if s:
            qs = qs.filter(
                Q(product__title__icontains=s)
                | Q(document__title__icontains=s)
                | Q(product__brand_name__icontains=s)
                | Q(product__manufacturer__icontains=s)
            ).distinct()
        if puc_kind and puc_kind != "all":
            if puc_kind == "none":
                qs = qs.filter(product__product_uber_puc__isnull=True)
            else:
                qs = qs.filter(product__product_uber_puc__puc__kind__code=puc_kind)
        if cm and cm != "all":
            qs = qs.filter(product__product_uber_puc__classification_method__code=cm)
        return qs


class ChemicalFunctionalUseListJson(BaseDatatableView):
    model = FunctionalUseToRawChem
    columns = [
        "chemical.extracted_text.data_document.data_group.group_type.title",
        "chemical.extracted_text.data_document.title",
        "functional_use.report_funcuse",
        "functional_use.category.title",
    ]

    def get_filter_method(self):
        return self.FILTER_ICONTAINS

    def get_initial_queryset(self):
        qs = (
            super()
            .get_initial_queryset()
            .select_related(
                "functional_use__category",
                "chemical__extracted_text__data_document__data_group__group_type",
            )
        )
        sid = self.request.GET.get("sid")
        if sid:
            return qs.filter(Q(chemical__dsstox__sid=sid)).distinct()
        return qs

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        puc = self.request.GET.get("puc")
        if puc:
            qs = qs.filter(
                Q(
                    chemical__extracted_text__data_document__products__product_uber_puc__puc=puc
                )
            )
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "chemical.extracted_text.data_document.title":
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                row.chemical.extracted_text.data_document.get_absolute_url(),
                value,
            )
        if column == "functional_use.category.title":
            if row.functional_use.category:
                return format_html(
                    '<a href="{}" title="Go to Functional Use Category detail" target="_blank">{}</a>',
                    row.functional_use.category.get_absolute_url(),
                    value,
                )
        if (
            column
            == "chemical.extracted_text.data_document.data_group.group_type.title"
        ):
            return format_html(
                '<span title="{}">{}</span>',
                row.chemical.extracted_text.data_document.data_group.group_type.description,
                value,
            )
        return value


class ChemicalLMAndHHDocumentJson(BaseDatatableView):
    model = UnionExtractedLMHHRec
    columns = [
        "rawchem.extracted_text.data_document.data_group.group_type.code",
        "rawchem.extracted_text.data_document.title",
        "medium",
        "harmonized_medium.name",
        "num_measure",
        "rawchem.chem_detected_flag",
    ]

    def get_filter_method(self):
        return self.FILTER_ICONTAINS

    def get_initial_queryset(self):
        sid = self.request.GET.get("sid")
        if sid:
            return UnionExtractedLMHHRec.objects.filter(rawchem__dsstox__sid=sid)
        return UnionExtractedLMHHRec.objects.exclude(rawchem__dsstox__isnull=True)

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "rawchem.extracted_text.data_document.title":
            doc = DataDocument.objects.get(
                id=row.rawchem.extracted_text.data_document.id
            )
            chem_pk = row.rawchem_id
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                doc.get_absolute_url() + "#chem-card-" + str(chem_pk),
                value,
            )
        elif column == "harmonized_medium.name":
            if row.harmonized_medium != None:
                return format_html(
                    '<a href="{}" title="Go to harmonized media detail" target="_blank">{}</a>',
                    row.harmonized_medium.get_absolute_url(),
                    value,
                )
        return value
