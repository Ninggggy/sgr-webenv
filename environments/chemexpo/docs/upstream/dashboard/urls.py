from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path

from dashboard.urls_internal import urlpatterns as urlpatterns_internal
import dashboard.views.data_group
import dashboard.views.functional_use_category
from factotum import app_type
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("datadocument/<int:pk>/", views.data_document_detail, name="data_document"),
    path(
        "datadocument/<int:pk>/cards",
        views.data_document_cards,
        name="data_document_cards",
    ),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("d_json/", views.DocumentListJson.as_view(), name="d_ajax_url"),
    path("p_json/", views.ProductListJson.as_view(), name="p_ajax_url"),
    path(
        "fu_puc_json/", views.PucFunctionalUseListJson.as_view(), name="fu_puc_ajax_url"
    ),
    path("c_json/", views.ChemicalListJson.as_view(), name="c_ajax_url"),
    path("fuc_p_json/", views.FUCProductListJson.as_view(), name="fuc_p_ajax_url"),
    path("fuc_d_json/", views.FUCDocumentListJson.as_view(), name="fuc_d_ajax_url"),
    path("fuc_c_json/", views.FUCChemicalListJson.as_view(), name="fuc_c_ajax_url"),
    path("sid_gt_json", views.sids_by_grouptype_ajax, name="sid_gt_json_url"),
    path("pucs/", views.puc_list, name="puc_list"),
    path("puc/<int:pk>/", views.puc_detail, name="puc_detail"),
    path(
        "puc_chemical_csv/<int:pk>/",
        views.download_puc_chemicals,
        name="puc_chemical_csv",
    ),
    path(
        "download_puc_products_weight_fractions_csv/<int:pk>/",
        views.download_puc_products_weight_fractions,
        name="download_puc_products_weight_fractions",
    ),
    path(
        "dl_documents_chemical/<str:sid>",
        views.download_documents_chemical,
        name="download_documents_chemical",
    ),
    path("dl_pucs_json/", views.bubble_PUCs, name="bubble_PUCs"),
    path(
        "puc_functional_uses_csv/<int:pk>/",
        views.download_puc_functional_uses,
        name="download_puc_functional_uses",
    ),
    path(
        "dl_pucs_json/tree/", views.collapsible_tree_PUCs, name="collapsible_tree_PUCs"
    ),
    path("dl_pucs/", views.download_PUCs, name="download_PUCs"),
    path(
        "dl_lp_chemicals/",
        views.download_list_presence_chemicals,
        name="download_LP_chemicals",
    ),
    path(
        "dl_co_chemicals/",
        views.download_composition_chemicals,
        name="download_CO_chemicals",
    ),
    path(
        "dl_pucs_chemicals/",
        views.download_pucs_chemicals,
        name="download_PUCS_chemicals",
    ),
    path("dl_puctags/", views.download_PUCTags, name="download_PUCTags"),
    path("dl_lpkeywords/", views.download_LPKeywords, name="download_LPKeywords"),
    path(
        "dl_functionalusecategories/",
        views.download_FunctionalUseCategories,
        name="download_FunctionalUseCategories",
    ),
    path(
        "dl_functional_uses/",
        views.download_functional_uses,
        name="download_functional_uses",
    ),
    path(
        "functional_use_categories/",
        views.functional_use_category_list,
        name="functional_use_category_list",
    ),
    path(
        "functional_use_category/<int:pk>/",
        views.functional_use_category_detail,
        name="functional_use_category_detail",
    ),
    path(
        "download_functional_use_category_products_csv/<int:pk>/",
        views.download_functional_use_category_products,
        name="download_functional_use_category_products",
    ),
    path(
        "download_functional_use_category_chemicals_csv/<int:pk>/",
        views.download_functional_use_category_chemicals,
        name="download_functional_use_category_chemicals",
    ),
    path("chemical/<str:sid>/", views.chemical_detail, name="chemical"),
    path(
        "dl_composition_chemical/<str:sid>/",
        views.chemical.download_composition_chemical,
        name="download_composition_chemical",
    ),
    path(
        "dl_documents_keyword/<int:pk>/",
        views.download_documents_keyword,
        name="download_documents_keyword",
    ),
    path(
        "dl_chemicals_keyword/<int:pk>/",
        views.download_chemicals_keyword,
        name="download_chemicals_keyword",
    ),
    path(
        "dl_functional_uses_chemical/<str:sid>/",
        views.download_functional_uses_chemical,
        name="download_functional_uses_chemical",
    ),
    path(
        "chemical_product_json/",
        views.ChemicalProductListJson.as_view(),
        name="chemical_product_ajax_url",
    ),
    path(
        "chemical_functional_use_json/",
        views.ChemicalFunctionalUseListJson.as_view(),
        name="chemical_functional_use_ajax_url",
    ),
    path("get_data/", views.get_data, name="get_data"),
    path("visualizations/", views.Visualizations.as_view(), name="visualizations"),
    path(
        "datadocument/<int:pk>/download_chemicals/",
        views.download_document_chemicals,
        name="download_document_chemicals",
    ),
    path("search/<str:model>/", views.search_model, name="search-model"),
    path(
        "list_presence_tags/",
        views.list_presence_tag_list,
        name="list_presence_tag_list",
    ),
    path(
        "list_presence_tag/<int:pk>/",
        views.ListPresenceTagViewDetails,
        name="lp_tag_detail",
    ),
    path(
        "list_presence_tag/<int:pk>/chemicals/",
        views.ListPresenceChemicalJson.as_view(),
        name="lp_chemicals",
    ),
    path(
        "list_presence_tag/<int:tag_pk>/documents/",
        views.ListPresenceDocumentsJson.as_view(),
        name="lp_documents",
    ),
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path("", include("django_prometheus.urls")),
    path("release_notes/", views.get_release_notes, name="release_notes"),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if app_type.is_internal():
    urlpatterns += urlpatterns_internal
