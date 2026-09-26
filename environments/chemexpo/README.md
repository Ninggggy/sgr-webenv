# ChemExpo / CPDat

Chemical and product search, product-use categories, linked records, visualizations and CSV downloads using CPDat 4.1.

From the repository root on Linux amd64:

```sh
python3 tools/build.py chemexpo --release v0.1.4
python3 tools/env.py prepare chemexpo --release v0.1.4 --local-images
python3 tools/env.py start chemexpo --release v0.1.4 --mode preview
```

Open http://127.0.0.1:8085/chemexpo/. Use `--mode eval` for the isolated browser.

```sh
python3 tools/env.py verify chemexpo --release v0.1.4
python3 tools/env.py reset chemexpo --release v0.1.4
python3 tools/env.py stop chemexpo --release v0.1.4
```

Data: [EPA CPDat](https://www.epa.gov/chemical-research/chemical-and-products-database-cpdat). Sources and collection dates accompany the data package. Collection and import scripts are in `tools/`. See [component notices](NOTICE.md).
