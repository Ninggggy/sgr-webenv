# WONDER query protection rules

The query layer applies small-count suppression, reliability markers and additional ancestor protection to results, charts and CSV exports.

## Category selection and propagation

When a selected cause category is suppressed, a displayed ancestor in the same group receives additional protection. Selecting a parent alone does not add unselected children. Protection does not propagate across different year/sex groups or unrelated branches.

Birth denominators are hidden on protected death rows. Overlapping cause categories are not combined into a total. The cause and leading-cause displays use their corresponding aggregation rules; see [query coverage](../environments/wonder/COVERAGE.md).

The additional ancestor and denominator protections are intentional local display rules. Refer to the [official linked-data help](https://wonder.cdc.gov/wonder/help/lbd-expanded.html) for source definitions and to the [data-use notice](../environments/wonder/licenses/DATA_USE_NOTICE.md) for applicable conditions.

## Running boundary tests

From the repository root:

```sh
python3 -m unittest discover -s tests -p test_wonder_protection.py -v
```

The suite covers count thresholds, weighted rounding, reliability markers, parent/child selections, unrelated branches, grouping boundaries, hidden rows and selection order. Use a separate author browser container for webpage checks so the agent browser retains its configured process and memory limits.
