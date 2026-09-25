# Public visibility and anonymous validation

Repository and Release are still private/draft. Authenticated image pull passed;
this is not anonymous installation acceptance. GHCR granular package visibility
is separate from repository visibility. The official REST package API does not
document a visibility-change operation; use each package's web **Package settings**
→ **Change visibility** → **Public** when publication is ready.

Never send an account token in chat. These packages contain application/browser
code, not the withheld WONDER databases or NOAA's proprietary chart component.

| Package | Current verified visibility |
|---|---|
| [sgr-webenv-runtime:1](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-runtime) | private |
| [sgr-webenv-browser-base:1](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-browser-base) | private |
| [sgr-webenv-census-web:0.2.1](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-census-web) | private |
| [sgr-webenv-census-browser:0.2](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-census-browser) | private |
| [sgr-webenv-wonder-web:0.3](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-wonder-web) | private |
| [sgr-webenv-wonder-browser:0.2](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-wonder-browser) | private |
| [sgr-webenv-arxiv-web:0.1.0](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-arxiv-web) | private |
| [sgr-webenv-arxiv-browser:0.1.0](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-arxiv-browser) | private |
| [sgr-webenv-arxiv-search:0.1.0](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-arxiv-search) | private |
| [sgr-webenv-wateroffice-web:0.1.0-dev](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-wateroffice-web) | private |
| [sgr-webenv-wateroffice-browser:0.1.0-dev](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-wateroffice-browser) | private |

The repository/Release must remain marked candidate until the declared checks
pass. Before publishing a stable tag, replace draft `untagged-...` asset URLs with
the final release URLs and verify every download. Anonymous tests must use no
GitHub or Docker credentials. Do not infer package visibility from source visibility.

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
assets and audit history are retained privately. Assets are being migrated.
Existing GHCR packages also need their connected repository checked after the
rename; the OCI source label alone is not evidence of that connection.

GitHub's [history-removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
explains that cached references may remain after a force-push and that Support
does not promise removal of non-sensitive data. Do not assume a support request
will solve this licensing-related object issue. No external message has been sent.
