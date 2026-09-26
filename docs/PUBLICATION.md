# Publication and anonymous validation

The source repository and all 11 `sgr-webenv-release-*` packages are public.
All 11 anonymous image pulls passed using an empty Docker credential directory.
Each public package page links to `Ninggggy/sgr-webenv`, not private staging.
See `verification/public-package-pages.json`. The old API-only association
attempts were inconclusive and are superseded by this public-page observation.

The v0.1.0 Release contains five cleared data attachments. The latest anonymous
source/data/image test is `verification/anonymous-publication.json`; full streamed
asset comparisons are recorded separately when completed. Cached Docker layers
may be reused; this is not independent-machine install evidence.

Census and arXiv keep their declared supported scope; Wateroffice remains a
development version. NOAA's proprietary chart component and WONDER's raw data
are withheld. Do not interpret public materials as complete five-site parity.

Package links are listed in `verification/public-package-pages.json` and image
names in `releases/v0.1.0.json`. For future versions, GitHub package visibility
must be checked separately from repository visibility.

Official instructions: https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility

## Private staging history and clean migration

A read-only check on 2026-09-26 confirmed that GitHub can still retrieve the
excluded ZingChart library through a removed initial commit. Main is clean, but
rewriting main did not remove the old server-side object. The affected repository is retained privately as
`sgr-webenv-private-staging`; it must not be made public. The issue is recorded in
`verification/remote-history-review.json` without republishing the library.

A safe publication route is a new repository containing only the current
whitelisted source snapshot, with no parent history or fork relationship to the
private staging repository. Retain the staging repository privately so its draft
assets, build evidence and rollback material are not lost; re-upload only cleared
assets to the clean repository. Repository names and GHCR associations would
need migration. The user authorized this migration. A new independent `sgr-webenv` repository
has been created and populated with a clean source snapshot; the excluded old
commit/file cannot be retrieved there. The previous staging repository, draft
assets and audit history are retained privately. All five cleared data assets have been migrated; their contents match the validated archives.
The old GHCR packages were not readable by the new repository token (HTTP 403).
The unchanged validated images have been published privately under `sgr-webenv-release-*`
so their package association can be established with the new repository. Old
packages remain untouched for rollback. Use only the **new package links above**
for public visibility settings. The OCI source label alone is not evidence of
the actual GitHub package/repository connection.

GitHub's [history-removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
explains that cached references may remain after a force-push and that Support
does not promise removal of non-sensitive data. Do not assume a support request
will solve this licensing-related object issue. No external message has been sent.
