# Public visibility and anonymous validation

The repository is now public; the Release remains a draft. All 11 new packages passed authenticated pulls. Eight now pass anonymous pulls
and their public package pages confirm association with this repository.
Three still return 404/unauthorized: wonder-web, arxiv-browser and arxiv-search. This is not anonymous installation acceptance. GHCR granular package visibility
is separate from repository visibility. The official REST package API does not
document a visibility-change operation; use each package's web **Package settings**
→ **Change visibility** → **Public** when publication is ready.

For each **new** package below, first check the linked repository on the package
page. It must be `Ninggggy/sgr-webenv`. If no repository is linked, choose
**Connect repository** and select the new `sgr-webenv`. If it points to private
staging, correct the connection in Package settings. Do not publish the staging
repository or old packages. The API checks could not establish this connection;
this is an unverified check, not a claim that the connection is absent.

Never send an account token in chat. These packages contain application/browser
code, not the withheld WONDER databases or NOAA's proprietary chart component.

| Package | Verified state / manual action |
|---|---|
| [sgr-webenv-release-runtime:1](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-release-runtime) | Public; anonymous pull and repository association verified |
| [sgr-webenv-release-browser-base:1](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-release-browser-base) | Public; anonymous pull and repository association verified |
| [sgr-webenv-release-census-web:0.2.1](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-release-census-web) | Public; anonymous pull and repository association verified |
| [sgr-webenv-release-census-browser:0.2](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-release-census-browser) | Public; anonymous pull and repository association verified |
| [sgr-webenv-release-wonder-web:0.3](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-release-wonder-web) | Private; check linked repository, then set Public |
| [sgr-webenv-release-wonder-browser:0.2](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-release-wonder-browser) | Public; anonymous pull and repository association verified |
| [sgr-webenv-release-arxiv-web:0.1.0](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-release-arxiv-web) | Public; anonymous pull and repository association verified |
| [sgr-webenv-release-arxiv-browser:0.1.0](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-release-arxiv-browser) | Private; check linked repository, then set Public |
| [sgr-webenv-release-arxiv-search:0.1.0](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-release-arxiv-search) | Private; check linked repository, then set Public |
| [sgr-webenv-release-wateroffice-web:0.1.0-dev](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-release-wateroffice-web) | Public; anonymous pull and repository association verified |
| [sgr-webenv-release-wateroffice-browser:0.1.0-dev](https://github.com/users/Ninggggy/packages/container/package/sgr-webenv-release-wateroffice-browser) | Public; anonymous pull and repository association verified |

The repository/Release must remain marked candidate until the declared checks
pass. The manifest uses final `v0.1.0` asset URLs. GitHub currently reports an internal `untagged-...` draft tag; set `v0.1.0` when publishing and verify every download. Anonymous tests must use no
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
