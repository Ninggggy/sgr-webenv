# Search and export semantics

## Search

The local analyzer uses Snowball English stemming with reference line-prefix removal. Punctuation separates terms; asterisks do not expand prefixes, and a colon within a phrase is not an API field selector. Exact-name promotion uses the literal query before punctuation processing.

Results sort by casefolded name and accession for stable equal-name ties. Large result sets remain complete rather than inheriting the original HTML display cap. API syntax and external services are separate from the core website search.

## STR results and exports

Marker-data source scope follows each marker's explicit sources. CSV and XLSX follow displayed profile-row order. JSON retains grouped scientific results and includes `rowOrder` as result/profile index pairs. Row-order inputs must be complete permutations without duplicates, omissions or invalid indices.

Best/Worst labels and source names are preserved. CSV quotes are escaped. Sort state is restored from the URL and cleared by session reset.
