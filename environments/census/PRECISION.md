# Numeric values, annotations and statistical populations

Archived formatted CSV cells retain their source precision. Summary File cells retain the fixed-year estimate and margin-of-error values. A missing source value is not zero.

Ordinary negative estimates are valid. Special codes are interpreted by channel: MOE -1 means no MOE; a Summary File dot retains its unavailable annotation; MOE 0 remains zero with its applicable controlled-estimate annotation.

Numeric filters, sorting and maps use exact-valued cells. Annotated medians retain their source bounds in exports; JSON carries the value and annotation separately. Interpret `median precision unresolved` cells using their annotations, and use exact-valued cells for exact-threshold comparisons.

## Task definitions

For 002, C16002 limited-English-speaking households use the full household population; B25003 renter households are a separate condition. The rent-burden numerator covers 35% or more of income, with `Not computed` excluded from the denominator.

For 004, the 65+ population and ambulatory-difficulty denominator use B18105 civilian noninstitutionalized residents. B01001 total residents are a different population. Other housing and household measures retain their own universes.

Use exact fractions for threshold comparisons and round only the final output. Read each table's universe and units before combining values. Margins of error follow the individual source tables.
