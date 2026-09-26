# WONDER data redistribution review

Reviewed 2026-09-26. **Project decision: release the audited national NCHS
public-use-derived runtime databases with the data-use notice below.** This
supersedes the earlier blanket hold based only on the existence of small cells.
It is a project interpretation of published terms, not individual permission
from CDC, a legal opinion, or a license for identifying people.

## Sources and applicable terms

1. The [official Vital Statistics Online portal](https://www.cdc.gov/nchs/data_access/vitalstatsonline.htm)
   separately distributes national public-use Natality and Period Linked
   Birth–Infant Death ZIP files for independent research. The reviewed inputs
   are Natality 2016–2024 and Period Linked 2017–2023, listed in
   `environments/wonder/sources/download-manifest.json`.
2. The [NVSS microdata release policy](https://www.cdc.gov/nchs/nvss/dvs_data_release.htm)
   distinguishes downloadable public-use microdata from interactive tabulations.
   Its post-2005 public files omit state/county/city identifiers and exact event
   dates. Interactive services may have additional geography and impose cell
   size limits. Our inputs are the national public-use files, not restricted
   geographic files or a reconstruction of suppressed WONDER responses.
3. The [NCHS public-use agreement](https://www.cdc.gov/nchs/policy/data-user-agreement.html)
   limits use to statistical reporting/analysis, forbids identifying people or
   establishments, linking to individually identifiable data, and research on
   re-identification or disclosure-protection methods. These restrictions are
   carried with the data; Apache-2.0 does not replace them. This agreement does
   not state a blanket ban on copying public-use files or a nine-count threshold
   for their storage representation.
4. [CDC agency-materials terms](https://www.cdc.gov/other/agencymaterials.html)
   generally permit reproduction of public-domain agency information subject to
   attribution, no implied endorsement, preservation of substantive content and
   notice that the original material is available free from CDC. Exceptions
   for third-party/state materials and logos still apply. This data archive
   contains numeric public-use-derived data and provenance, no logo, font,
   third-party media, state-issued certificates or restricted records. Our
   selected fields, recodings and aggregation are documented as project
   processing, not an unchanged official CDC publication.
5. [WONDER data-use restrictions](https://wonder.cdc.gov/datause.html) prohibit
   publication of small birth/death statistics (nine or fewer), including
   associated rates. We retain those restrictions for the reproduced query
   interface and its exports. They are not evidence that every national NCHS
   public-use microdata record must be removed before redistribution. No
   unsuppressed query capture from WONDER is included in this archive.

## What is being released

Sixteen SQLite files retain selected national public-use fields as grouped
records with multiplicities and, for linked death records, original weighting
information. The grouping is a compact representation for further statistical
queries; it is not an official WONDER output table. Names, addresses, record
identifiers, institution identifiers, state/county/city identifiers and exact
calendar event dates are not columns in these databases. `place` is a delivery
setting category; `death_days` is infant age at death, not a calendar date.
No attempt to identify anyone or evaluate disclosure methods is part of this
review. Schema/provenance inspection is not a re-identification-risk guarantee.

For 2021 Natality, the installed database uses the same-year **public** linked
birth denominator, not death records, to restore the origin field. The importer
uses the documented public birthweight imputation flag to preserve the original
not-stated category. Prior author verification established equality with the
original Natality joint distribution after coarsening the origin category.
This is explicitly disclosed; neither restricted files nor suppressed WONDER
values are used to fill the database. The release preserves that already-tested
installed version rather than rerunning reconstruction or modifying counts.

The included record multiplicities can be 1–9. Their existence alone was an
insufficient reason to characterize this archive as prohibited WONDER query
redistribution. They come from already released national public-use inputs and
contain no fields added by joining to identifiable or restricted sources.
Website suppression, reliability markers and conservative parent protection
remain unchanged. Users must not treat raw runtime tables as publication-ready
small-cell statistics or claim that the offline service is CDC-endorsed.

## Conditions of this release

- Attribute CDC/NCHS NVSS; originals are available without charge from CDC.
- Preserve the accompanying data-use notice when redistributing the archive.
- Statistical reporting and analysis only; preserve NCHS prohibitions above.
- Do not misrepresent project recodings as an unmodified official dataset.
- Keep the website/export small-cell protections; do not use this release to
  identify people or reconstruct suppressed geographic WONDER information.
- No new restricted data, raw web query captures, author answers or credentials
  may be added under this review's conclusion.

The data are not relicensed Apache-2.0, CC0, or as unrestricted research data.
No special permission was requested, no external messages were sent, and no
rights beyond the published source terms are claimed. A different dataset or
purpose requires its own assessment. Review evidence and packaging checks are
in `docs/verification/wonder-data-release.json`.
