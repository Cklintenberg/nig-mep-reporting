# Scoring correction before holdout

The first development outputs exposed an overly strict provenance scorer: a model citing both the correct value row and a valid context/header row was marked wrong. Scorer v2 requires at least one gold value-bearing reference and all references to exist in the supplied source list. It still rejects a header alone or unknown reference IDs. This correction applies identically to all candidates; the prompt, schema, fixtures and gold values are unchanged. Per-call original scores are retained, and the final report recomputes v2 scores from raw outputs. Holdout was not inspected before this correction.

Raw accuracy, provenance, restriction/injection flags, and critical-value safety are reported separately so a harmless extra-context reference cannot be confused with a wrong number. The mechanical validator cannot prove semantic truth or provider confidentiality.

## Precision distinction after holdout inspection

The frozen numeric comparator uses relative/absolute tolerance 1e-7. Haiku returned 1.3333 hours for 80 minutes in holdout case 40, while gold stores 1.3333333333333333. The strict score remains failed. The report additionally labels differences of at most 0.0001 for continuous hours/percent fields as rounding-only, separately from substantive incorrect values. This post-run descriptive breakdown is not a new passing gate and does not alter gold, prompts, case passes or field accuracy. Counts remain exact. A follow-up benchmark should predefine business precision and move arithmetic/unit conversions into deterministic code.
