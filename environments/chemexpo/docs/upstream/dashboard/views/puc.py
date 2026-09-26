from django.shortcuts import render, get_object_or_404
from dashboard.models import (
    PUC,
    DSSToxLookup,
    ExtractedComposition,
    FunctionalUseToRawChem,
)
from dashboard.utils import get_download_filename, render_to_csv_response
from django.db.models import Count, Q
from factotum.settings import DOWNLOADS_ROOT
import os
from django.http import FileResponse, HttpResponse

from factotum.app_type import select_template_for_app


def puc_list(request, template_name="puc/puc_list.html"):
    pucs = (
        PUC.objects.all()
        .values("kind__name", "gen_cat", "prod_fam", "prod_type", "id", "description")
        .annotate(product_count=Count("productuberpuc"))
        .order_by("kind__name", "gen_cat", "prod_fam", "prod_type")
    )
    data = {}
    data["pucs"] = list(pucs)
    return render(request, template_name, data)


def puc_detail(
    request,
    pk,
    template_name=select_template_for_app(
        internal="puc/puc_detail_internal.html", external="puc/puc_detail.html"
    ),
):
    puc = get_object_or_404(PUC, pk=pk)
    data = {"puc": puc, "linked_taxonomies": puc.get_linked_taxonomies()}
    return render(request, template_name, data)


def download_puc_functional_uses(request, pk):
    puc = get_object_or_404(PUC, pk=pk)
    fn = FunctionalUseToRawChem.objects.filter(
        chemical__extracted_text__data_document__product__product_uber_puc__puc_id=puc
    ).values(
        "chemical__extracted_text__data_document__id",
        "chemical__extracted_text__data_document__title",
        "chemical__raw_chem_name",
        "chemical__raw_cas",
        "chemical__dsstox__sid",
        "chemical__dsstox__true_chemname",
        "chemical__dsstox__true_cas",
        "functional_use__report_funcuse",
        "functional_use__category__title",
    )

    filename = get_download_filename(
        puc.__str__().replace(" ", "_") + "_functional_uses", "csv"
    )
    return render_to_csv_response(
        fn,
        filename=filename,
        field_header_map={
            "chemical__extracted_text__data_document__id": "Data Document ID",
            "chemical__extracted_text__data_document__title": "Data Document Title",
            "chemical__raw_chem_name": "Raw Chemical Name",
            "chemical__raw_cas": "Raw CAS",
            "chemical__dsstox__sid": "DTXSID",
            "chemical__dsstox__true_chemname": "Curated Chemical Name",
            "chemical__dsstox__true_cas": "Curated CAS",
            "functional_use__report_funcuse": "Reported Function",
            "functional_use__category__title": "Harmonized Function",
        },
    )


def download_puc_chemicals(request, pk):
    puc = get_object_or_404(PUC, pk=pk)
    chemicals = (
        DSSToxLookup.objects.filter(
            curated_chemical__extracted_text__data_document__product__product_uber_puc__puc=puc
        )
        .annotate(
            manual_count=Count(
                "curated_chemical",
                filter=Q(
                    curated_chemical__extracted_text__data_document__product__product_uber_puc__classification_method__code__in=(
                        "MA",
                        "AC",
                        "MB",
                        "BA",
                    )
                ),
            )
        )
        .annotate(
            auto_count=Count(
                "curated_chemical",
                filter=Q(
                    curated_chemical__extracted_text__data_document__product__product_uber_puc__classification_method__code="AU"
                ),
            )
        )
        .values("sid", "true_cas", "true_chemname", "manual_count", "auto_count")
    )
    filename = get_download_filename(
        puc.__str__().replace(" ", "_") + "_chemicals", "csv"
    )
    return render_to_csv_response(
        chemicals,
        filename=filename,
        field_header_map={
            "sid": "DTXSID",
            "true_chemname": "Curated Chemical Name",
            "true_cas": "Curated CAS",
            "manual_count": "Manual Count",
            "auto_count": "Auto Count",
        },
    )


def download_pucs_chemicals(request):
    # add_timestamp=False because we don't want to add a new file every day; we want to overwrite the old one
    internal_filename = get_download_filename(
        "bulk_PUCS_chemicals", "zip", add_timestamp=False
    )
    filepath = os.path.join(DOWNLOADS_ROOT, internal_filename)
    if os.path.exists(filepath):
        external_filename = get_download_filename(
            "bulk_PUCS_chemicals", "zip", add_timestamp=True
        )
        return FileResponse(
            open(filepath, "rb"), filename=external_filename, as_attachment=True
        )
    else:
        return HttpResponse(
            f"Product Category Data not available yet, please try again later.",
            status=404,
        )


def download_puc_products_weight_fractions(request, pk):
    puc = get_object_or_404(PUC, pk=pk)
    chems = (
        ExtractedComposition.objects.filter(
            extracted_text__data_document__products__product_uber_puc__puc=puc
        )
        .prefetch_related("weight_fraction_type", "unit_type")
        .values(
            "extracted_text__data_document__id",
            "extracted_text__data_document__title",
            "extracted_text__doc_date",
            "extracted_text__data_document__products__title",
            "extracted_text__data_document__products__product_uber_puc__classification_method__name",
            "extracted_text__data_document__products__tags_name",
            "raw_chem_name",
            "raw_cas",
            "dsstox__sid",
            "dsstox__true_chemname",
            "dsstox__true_cas",
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
        .distinct()
        .order_by(
            "extracted_text__data_document__title",
            "extracted_text__data_document__products__title",
            "raw_chem_name",
        )
    )
    filename = get_download_filename(
        puc.__str__().replace(" - ", "_") + "_products_and_weight_fractions", "csv"
    )
    return render_to_csv_response(
        chems,
        filename=filename,
        use_verbose_names=False,
        field_header_map={
            "extracted_text__data_document__id": "Data Document ID",
            "extracted_text__data_document__title": "Data Document Title",
            "extracted_text__doc_date": "Document Date",
            "extracted_text__data_document__products__title": "Product Name",
            "extracted_text__data_document__products__product_uber_puc__classification_method__name": "PUC Classification Method",
            "extracted_text__data_document__products__tags_name": "Attributes",
            "raw_chem_name": "Raw Chemical Name",
            "raw_cas": "Raw CAS Number",
            "dsstox__sid": "DTXSID",
            "dsstox__true_chemname": "Curated Chemical Name",
            "dsstox__true_cas": "Curated CAS Number",
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
