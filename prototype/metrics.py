"""Deterministic calculations: the LLM never computes the report's numbers."""
from datetime import timedelta
from io import BytesIO
import math
import pandas as pd
from schemas import Issue, MetricResult, SourcePack

DEFINITIONS = {
    "weekly_active_users": ("Weekly active users", "users", "relative %"),
    "availability": ("Platform availability", "%", "percentage points"),
    "analytics_freshness": ("Analytics delay", "hours", "hours"),
    "api_error_rate": ("API error rate", "%", "percentage points"),
}
COLUMNS = {"week_start", "cohort", "metric", "value", "unit"}


def calculate_metrics(raw: bytes, pack: SourcePack):
    if len(raw) > 1_000_000:
        raise ValueError("Metrics CSV exceeds the 1 MB prototype limit.")
    try:
        df = pd.read_csv(BytesIO(raw), dtype=str, keep_default_na=False)
    except Exception as exc:
        raise ValueError("Cannot read metrics.csv. Check the CSV format.") from exc
    if set(df.columns) != COLUMNS:
        raise ValueError("metrics.csv requires exactly: week_start, cohort, metric, value, unit.")
    if len(df) > 500:
        raise ValueError("Metrics CSV exceeds the 500-row prototype limit.")
    for col in df:
        df[col] = df[col].str.strip()
    if df.empty:
        raise ValueError("Metrics CSV is empty.")
    if df.duplicated(["week_start", "cohort", "metric"]).any():
        raise ValueError("Duplicate metric rows: do not sum already-aggregated values.")
    if (df.cohort == "").any() or df.cohort.nunique() != 1:
        raise ValueError("Use one named application cohort per report. Distinct users cannot be added across cohorts.")
    weeks = [(pack.week_start - timedelta(days=7)).isoformat(), pack.week_start.isoformat()]
    if not set(df.week_start).issubset(set(weeks)):
        raise ValueError("CSV dates must match the report's Monday and the previous Monday.")
    if not set(df.metric).issubset(DEFINITIONS):
        raise ValueError("CSV contains an unsupported metric.")
    values = []
    for i, row in df.iterrows():
        label, unit, _ = DEFINITIONS[row.metric]
        if row.unit != unit:
            raise ValueError(f"CSV row {i + 2}: {label} requires unit '{unit}'.")
        try:
            value = float(row.value)
        except ValueError as exc:
            raise ValueError(f"CSV row {i + 2}: value must be a number. Omit unavailable rows.") from exc
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"CSV row {i + 2}: value must be finite and nonnegative.")
        if unit == "%" and value > 100:
            raise ValueError(f"CSV row {i + 2}: percentage must be between 0 and 100.")
        if unit == "users" and not value.is_integer():
            raise ValueError(f"CSV row {i + 2}: user count must be an integer.")
        values.append(value)
    df["number"] = values
    results, issues = [], []
    for key, (label, unit, delta_kind) in DEFINITIONS.items():
        rows = df[df.metric == key]
        counts = [rows.loc[rows.week_start == w, "number"].tolist() for w in weeks]
        previous, current = [v[0] if v else None for v in counts]
        delta = None
        if current is None or previous is None:
            issues.append(Issue(severity="warning", code="missing_metric", message=f"{label}: missing {'current' if current is None else 'previous'} week data. No change calculated."))
        elif delta_kind == "relative %":
            if previous == 0:
                issues.append(Issue(severity="warning", code="zero_baseline", message=f"{label}: prior value is zero. Relative change is undefined."))
            else:
                delta = round((current - previous) / previous * 100, 4)
        else:
            delta = round(current - previous, 4)
        results.append(MetricResult(key=key, label=label, unit=unit, previous=previous, current=current,
            delta=delta, delta_kind=delta_kind, previous_period=weeks[0], current_period=weeks[1],
            cohort=str(df.cohort.iloc[0]), source_rows=[int(i) + 2 for i in rows.index]))
    return results, issues
