# Run and manage an environment

Use Linux amd64, Docker Engine with Compose v2 and Python 3.9+. Run commands from the repository root.

```sh
python3 tools/env.py prepare census --release v0.1.4
python3 tools/env.py start census --release v0.1.4 --mode preview
python3 tools/env.py verify census --release v0.1.4
python3 tools/env.py reset census --release v0.1.4
python3 tools/env.py stop census --release v0.1.4
```

Replace `census` with the selected environment. NOAA and ChemExpo use the setup commands in their environment READMEs. Preview ports are listed in the root README; use `--mode eval` for the isolated browser.

`verify` checks service health. `reset` clears sessions and downloads while retaining data. `stop` stops the instance. Use the same `--release` value for all commands.

Data and configuration are stored under `.state/<release>/<site>`. Set `--state-dir /your/writable/path` on every command to choose another location, and `--port` to choose a preview port. Preview listens on `127.0.0.1`; forward this port through SSH when using a remote host.

Reserve disk space for archives, extracted data, images and indexes, keeping 5 GiB free during preparation. arXiv preparation builds its search index; its search container uses a 24 GiB memory limit. Keep releases in separate state directories and stop an instance before reusing its port.

For source builds, run `python3 tools/build.py <site> --release v0.1.4`, then add `--local-images` to `prepare`. A local data archive can be supplied with `--data-archive /path/to/data.tar.gz`.
