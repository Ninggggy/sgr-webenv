# Wateroffice data and interface guide

The environment provides station search, historical observations, archived realtime observations, reference pages, maps and downloads.

## Data sources and time ranges

- Historical data: official HYDAT release 2026-07-17, including monthly flags, daily values, zeros and quality symbols.
- Realtime data: 2,248 catalog stations; official CSV observations for 483 stations cover 2026-08-26 09:40 UTC through 2026-09-25 09:40 UTC, and 1,765 stations use seven-day GeoMet snapshots. Station metadata records the observation intervals.
- Daily means and watch-list summaries: separate official source snapshots with their own collection timestamps.
- Station datum/reference pages: archived official HTML for the historical/realtime station union.

Station pages show source-provided Approval, Grade and Qualifiers. Dates, graphs and exports use the same per-station snapshot, preserving source values and blank fields.

## Maps and search

Maps use Leaflet and archived NRCan Toporama tiles, with national overview, five river-region detail areas and official basin polygons. Zoom levels follow the archived Toporama tiles.

Search filters use the archived source memberships. Filter combinations follow the archived query coverage. Coordinate and area filters use the source's geographic definitions.

## Tables, graphs and downloads

Historical workflows include daily, monthly and annual extreme values, statistics, datum pages and remarks. Realtime graphs can combine unit water level and discharge on dual axes; daily means are separate series.

Downloads contain the full selected set rather than only the displayed page. Empty map filters export a header-only file. URL state restores graph/table/download parameters across refresh, copied links and browser history.

## Session lists and operation

Quick lists support parameter selection, rename, individual-parameter removal and list deletion. Watch lists use the archived national summary, including unavailable entries.

Use the shared [installer and operation guide](../../docs/OPERATIONS.md). Preview binds to loopback, while evaluation uses the internal network. Reset clears saved lists, browser session state and transient downloads while retaining datasets. Source collectors, task answers and author evidence stay outside runtime mounts.
