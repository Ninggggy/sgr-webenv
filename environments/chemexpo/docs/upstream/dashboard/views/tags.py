from django.views.generic import DetailView
from django.shortcuts import render
from dashboard.models import (
    ExtractedListPresenceTag,
    ExtractedCPCat,
    ExtractedListPresenceToTag,
    ExtractedListPresence,
)
from django.db import models
from dashboard.utils import get_download_filename, render_to_csv_response
from django.db.models import Q, Subquery


def list_presence_tag_list(request, template_name="tags/tag_list.html"):
    tags = (
        ExtractedListPresenceTag.objects.all()
        .select_related("kind")
        .values("kind__name", "name", "definition", "id")
    )
    doc_counts = []
    for tagset in tags:
        qs = ExtractedCPCat.objects.filter(
            rawchem__extractedlistpresence__tags__pk=tagset["id"]
        ).distinct()
        doc_counts.append(models.When(pk=tagset["id"], then=qs.count()))

    tags = tags.annotate(
        Document_Count=models.Case(
            *doc_counts, default=0, output_field=models.CharField()
        )
    )
    data = {"tags": list(tags)}
    return render(request, template_name, data)


class ListPresenceTagView(DetailView):
    template_name = "tags/tag_detail.html"
    model = ExtractedListPresenceTag


def ListPresenceTagViewDetails(request, pk, template_name="tags/tag_detail.html"):
    my_list_presence_tags = ExtractedListPresenceTag.objects.get(pk=pk)

    tagsets = my_list_presence_tags.get_tagsets()
    tagsets = my_list_presence_tags.check_related_docs(tagsets)

    context = {
        "keysets": tagsets,
        "my_list_presence_tags": my_list_presence_tags,
        "keysets_ids": my_list_presence_tags.final_docs[pk],
    }
    return render(request, template_name, context)


def download_documents_keyword(request, pk):
    my_list_presence_tags = ExtractedListPresenceTag.objects.get(pk=pk)
    tagsets = my_list_presence_tags.get_tagsets()

    whens = {}
    whens["tag_names"] = []
    for c in my_list_presence_tags.ELPToTag_tags[pk]:
        whens["tag_names"].append(
            models.When(
                Q(pk=c),
                then=models.Value(my_list_presence_tags.ELPToTag_tags[pk][c]),
            )
        )
    qs = (
        ExtractedListPresence.objects.filter(
            pk__in=my_list_presence_tags.ELPToTag_tags[pk]
        )
        .values(
            "extracted_text__data_document__pk",
            "extracted_text__data_document__title",
            "extracted_text__doc_date",
        )
        .distinct()
        .annotate(
            tagset=models.Case(
                *whens["tag_names"], default=0, output_field=models.CharField()
            )
        )
    )

    # and print that to csv
    filename = get_download_filename(my_list_presence_tags.name + "_documents", "csv")
    return render_to_csv_response(
        qs,
        filename=filename,
        use_verbose_names=False,
        field_header_map={
            "extracted_text__data_document__pk": "Data Document ID",
            "extracted_text__data_document__title": "Data Document Title",
            "extracted_text__doc_date": "Document Date",
            "tagset": "Tagset",
        },
    )


def download_chemicals_keyword(request, pk):
    my_list_presence_tags = ExtractedListPresenceTag.objects.get(pk=pk)

    tagsets = my_list_presence_tags.get_tagsets()
    chems = my_list_presence_tags.get_dsstox(tagsets).values(
        "sid", "true_cas", "true_chemname"
    )

    filename = get_download_filename(my_list_presence_tags.name + "_chemicals", "csv")
    return render_to_csv_response(
        chems,
        filename=filename,
        use_verbose_names=False,
        field_header_map={
            "sid": "DTXSID",
            "true_cas": "Curated CAS",
            "true_chemname": "Curated Chemical name",
        },
    )
