# Operation and resource requirements

Use Linux amd64, Docker Engine with Compose v2 and Python 3.9+. Run commands from the repository root and specify `--release v0.1.3`.

## Preview and evaluation

`start --mode preview` binds the environment's port to `127.0.0.1`. For a remote host, forward that port through SSH. `start --mode eval` runs the isolated evaluation environment. Use the browser service's bridge protocol to interact with it.

`verify` checks service health. `reset` recreates transient containers and clears sessions and downloads, preserving datasets and the arXiv index. `stop` removes the instance's containers and network while retaining data.

State is stored under `.state/<release>/<site>`. Use the same `--state-dir /your/writable/path` on every command to change this location. Use `--port 18084`, for example, to assign a separate preview port.

## Resources

Reserve space for compressed downloads, extracted data, images and indexes. Keep at least 5 GiB free during preparation.

arXiv uses a search container with a 24 GiB memory limit and a 2 GiB Java heap, plus its web/browser services. Preparation builds a persistent search index. Use `start` to reuse it.

Cellosaurus container memory limits total approximately 5.2 GiB. Its extracted data occupy approximately 528 MiB. Wateroffice needs roughly 2 GiB for extracted data. Allow additional storage for image layers and build caches.

## Local builds and data

```sh
python3 tools/build.py base
python3 tools/build.py census
python3 tools/env.py prepare census --release v0.1.3 --local-images --data-archive /path/to/census-data-v0.1.0.tar.gz
```

For NOAA, use the [dedicated local-build instructions](../environments/noaa/README.md). [Data preparation](REBUILDING.md) describes source inputs.

## Switching versions

Keep each release in its own state directory. Stop the running instance before reusing its port, then start the selected release with its corresponding `--release` value. Retain the earlier data and images for rollback. Use the supplied `reset` and `stop` commands for lifecycle management.
