# Numeric values, annotations and statistical populations

Archived formatted CSV cells retain their source precision. Summary File cells retain the fixed-year estimate and margin-of-error values. A missing source value is not zero.

Ordinary negative estimates are valid. Special codes are interpreted by channel: MOE -1 means no MOE; a Summary File dot retains its unavailable annotation; MOE 0 remains zero with its applicable controlled-estimate annotation.

Annotated medians are not treated as exact values in numeric filtering, sorting or maps. Exports preserve annotations; JSON preserves the value and annotation separately. Values marked `median precision unresolved` should be excluded from exact-threshold tasks unless interpreting the bound is part of the task.

## Task definitions

For 002, C16002 limited-English-speaking households use the full household population; B25003 renter households are a separate condition. The rent-burden numerator covers 35% or more of income, with `Not computed` excluded from the denominator.

For 004, the 65+ population and ambulatory-difficulty denominator use B18105 civilian noninstitutionalized residents. B01001 total residents are a different population. Other housing and household measures retain their own universes.

Use exact fractions for threshold comparisons and round only the final output. Read each table's universe and units before combining values. Derived cross-table margins of error are not supplied.
