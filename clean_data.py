from pathlib import Path
import pandas as pd
import re


# ============================================================
# SCADA Alarm Gateway & Migrator
# Data ingestion, cleaning and normalization
# ============================================================


# ----------------------------------------------------------------
# Paths
# ----------------------------------------------------------------

# Carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent

RAW_FILE = BASE_DIR / "data" / "raw" / "alarms_raw.csv"
CLEAN_DIR = BASE_DIR / "data" / "clean"

CLEAN_DIR.mkdir(parents=True, exist_ok=True)

CLEAN_FILE = CLEAN_DIR / "alarms_clean.csv"
REJECTED_FILE = CLEAN_DIR / "alarms_rejected.csv"
DUPLICATES_FILE = CLEAN_DIR / "alarms_duplicates.csv"
QUALITY_REPORT_FILE = CLEAN_DIR / "quality_report.txt"


# ----------------------------------------------------------------
# Allowed values
# ----------------------------------------------------------------

VALID_TAGS = {
    "LT-101",
    "TT-101",
    "PT-101",
    "FT-101",
    "P-101",
    "P-102",
    "V-101",
    "M-101",
}

VALID_ALARM_TYPES = {
    "NORMAL",
    "LOW_LEVEL",
    "HIGH_LEVEL",
    "HIGH_TEMPERATURE",
    "LOW_PRESSURE",
    "HIGH_PRESSURE",
    "LOW_FLOW",
    "HIGH_FLOW",
    "PUMP_FAILURE",
    "COMMUNICATION_LOST",
    "VALVE_FAILURE",
    "HIGH_CURRENT",
    "MOTOR_FAILURE",
}

VALID_SEVERITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}

VALID_STATUSES = {
    "ACTIVE",
    "ACKNOWLEDGED",
    "CLEARED",
}


# ----------------------------------------------------------------
# Expected value types
# ----------------------------------------------------------------

NUMERIC_ALARM_TYPES = {
    "NORMAL",
    "LOW_LEVEL",
    "HIGH_LEVEL",
    "HIGH_TEMPERATURE",
    "LOW_PRESSURE",
    "HIGH_PRESSURE",
    "LOW_FLOW",
    "HIGH_FLOW",
    "VALVE_FAILURE",
    "HIGH_CURRENT",
}

STATE_VALUES = {
    "RUNNING",
    "STOPPED",
}


# ----------------------------------------------------------------
# Tag normalization
# ----------------------------------------------------------------

def normalize_tag(value):
    """
    Normalize legacy tag representations.

    Examples:
        'P_101' -> 'P-101'
        'P 101' -> 'P-101'
        ' p-101 ' -> 'P-101'
        'lt-101' -> 'LT-101'
    """

    if pd.isna(value):
        return pd.NA

    value = str(value).strip().upper()

    # Replace separators with '-'
    value = re.sub(r"[\s_]+", "-", value)

    return value


# ----------------------------------------------------------------
# Generic text normalization
# ----------------------------------------------------------------

def normalize_text(value):
    """
    Strip spaces and convert text to uppercase.
    """

    if pd.isna(value):
        return pd.NA

    value = str(value).strip().upper()

    if value in {"", "NAN", "NONE", "NULL", "N/A"}:
        return pd.NA

    return value


# ----------------------------------------------------------------
# Timestamp normalization
# ----------------------------------------------------------------

def normalize_timestamp(value):
    """
    Normalize legacy timestamps using explicit supported formats.

    Explicit parsing avoids ambiguity between DD/MM and MM/DD
    representations.

    Invalid timestamps become NaT.
    """

    if pd.isna(value):
        return pd.NaT

    value = str(value).strip()

    if value == "":
        return pd.NaT

    formats = [
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%b %d, %Y %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%d-%m-%Y %H:%M",
    ]

    for fmt in formats:
        try:
            return pd.to_datetime(value, format=fmt)
        except (ValueError, TypeError):
            continue

    return pd.NaT


# ----------------------------------------------------------------
# Value normalization
# ----------------------------------------------------------------

def normalize_value(value):
    """
    Normalize the value column.

    Numeric values remain numeric.
    Equipment states such as RUNNING and STOPPED remain strings.
    Invalid legacy values become missing.
    """

    if pd.isna(value):
        return pd.NA

    value = str(value).strip().upper()

    if value in {"", "NAN", "NONE", "NULL", "N/A", "ERROR"}:
        return pd.NA

    # Equipment state
    if value in STATE_VALUES:
        return value

    # Numeric value
    try:
        numeric_value = float(value)

        # Avoid displaying 10.0 when the original value
        # represents an integer.
        if numeric_value.is_integer():
            return int(numeric_value)

        return numeric_value

    except (ValueError, TypeError):
        return value


# ----------------------------------------------------------------
# Value classification
# ----------------------------------------------------------------

def classify_value(value):
    """
    Classify normalized values as:
        NUMERIC
        STATE
        NULL
        TEXT
    """

    if pd.isna(value):
        return "NULL"

    if isinstance(value, (int, float)):
        return "NUMERIC"

    if str(value).upper() in STATE_VALUES:
        return "STATE"

    return "TEXT"


# ----------------------------------------------------------------
# Load raw dataset
# ----------------------------------------------------------------

def load_raw_data():
    print()
    print("Loading raw dataset...")
    print(f"Input: {RAW_FILE}")

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Raw dataset not found: {RAW_FILE}"
        )

    # Read everything as string initially.
    # This is important because the raw dataset intentionally
    # contains mixed types and malformed values.
    df = pd.read_csv(
        RAW_FILE,
        dtype=str,
        keep_default_na=False,
    )

    print(f"Rows loaded: {len(df):,}")

    return df


# ----------------------------------------------------------------
# Validate columns
# ----------------------------------------------------------------

def validate_columns(df):
    required_columns = {
        "timestamp",
        "tag_name",
        "alarm_type",
        "severity",
        "value",
        "status",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(sorted(missing_columns))
        )


# ----------------------------------------------------------------
# Clean and normalize
# ----------------------------------------------------------------

def clean_data(df):
    print()
    print("Cleaning and normalizing data...")

    # Keep original row number for traceability.
    df.insert(0, "source_row", range(2, len(df) + 2))

    # Preserve original values before normalization.
    df["timestamp_raw"] = df["timestamp"]
    df["tag_name_raw"] = df["tag_name"]
    df["severity_raw"] = df["severity"]
    df["status_raw"] = df["status"]
    df["value_raw"] = df["value"]

    # Normalize fields.
    df["timestamp"] = df["timestamp"].apply(normalize_timestamp)
    df["tag_name"] = df["tag_name"].apply(normalize_tag)
    df["alarm_type"] = df["alarm_type"].apply(normalize_text)
    df["severity"] = df["severity"].apply(normalize_text)
    df["status"] = df["status"].apply(normalize_text)
    df["value"] = df["value"].apply(normalize_value)

    # ------------------------------------------------------------
    # Quality flags
    # ------------------------------------------------------------

    df["quality_flags"] = ""

    def add_flag(condition, flag):
        df.loc[condition, "quality_flags"] = (
            df.loc[condition, "quality_flags"]
            .apply(
                lambda current:
                f"{current};{flag}".strip(";")
            )
        )

    # Missing/invalid timestamp
    add_flag(
        df["timestamp"].isna(),
        "INVALID_TIMESTAMP"
    )

    # Invalid tags
    add_flag(
        ~df["tag_name"].isin(VALID_TAGS),
        "INVALID_TAG"
    )

    # Invalid alarm types
    add_flag(
        ~df["alarm_type"].isin(VALID_ALARM_TYPES),
        "INVALID_ALARM_TYPE"
    )

    # Invalid severities
    add_flag(
        ~df["severity"].isin(VALID_SEVERITIES),
        "INVALID_SEVERITY"
    )

    # Invalid statuses
    add_flag(
        ~df["status"].isin(VALID_STATUSES),
        "INVALID_STATUS"
    )

    # Missing value
    add_flag(
        df["value"].isna(),
        "MISSING_VALUE"
    )

    # ------------------------------------------------------------
    # Validate value against alarm type
    # ------------------------------------------------------------

    numeric_expected = df["alarm_type"].isin(
        NUMERIC_ALARM_TYPES
    )

    numeric_values = pd.to_numeric(
        df["value"],
        errors="coerce"
    )

    # Numeric alarm with non-numeric value
    invalid_numeric_value = (
        numeric_expected
        & df["value"].notna()
        & numeric_values.isna()
    )

    add_flag(
        invalid_numeric_value,
        "INVALID_NUMERIC_VALUE"
    )

    # Pump normal/failure events should contain RUNNING/STOPPED
    pump_events = df["tag_name"].isin({"P-101", "P-102"})

    expected_pump_state = (
        pump_events
        & df["alarm_type"].isin(
            {"NORMAL", "PUMP_FAILURE"}
        )
        & df["value"].notna()
    )

    invalid_pump_state = (
        expected_pump_state
        & ~df["value"].isin(STATE_VALUES)
    )

    add_flag(
        invalid_pump_state,
        "INVALID_PUMP_STATE"
    )

    # Communication lost can legitimately have a NULL value.
    # Therefore we do NOT reject it automatically.

    # ------------------------------------------------------------
    # Value type
    # ------------------------------------------------------------

    df["value_type"] = df["value"].apply(
        classify_value
    )

    # ------------------------------------------------------------
    # Timestamp formatting
    # ------------------------------------------------------------

    # Use a consistent representation for the clean dataset.
    df["timestamp"] = df["timestamp"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return df


# ----------------------------------------------------------------
# Duplicate detection
# ----------------------------------------------------------------

def detect_duplicates(df):
    """
    Detect exact duplicate records after normalization.
    """

    duplicate_columns = [
        "timestamp",
        "tag_name",
        "alarm_type",
        "severity",
        "value",
        "status",
    ]

    duplicate_mask = df.duplicated(
        subset=duplicate_columns,
        keep="first",
    )

    duplicates = df.loc[duplicate_mask].copy()

    clean_df = df.loc[~duplicate_mask].copy()

    return clean_df, duplicates


# ----------------------------------------------------------------
# Rejected records
# ----------------------------------------------------------------

def separate_rejected_records(df):
    """
    Separate records with critical validation errors.

    A missing value by itself is NOT considered enough to reject
    a row because COMMUNICATION_LOST legitimately produces NULL.
    """

    critical_flags = [
        "INVALID_TIMESTAMP",
        "INVALID_TAG",
        "INVALID_ALARM_TYPE",
        "INVALID_SEVERITY",
        "INVALID_STATUS",
        "INVALID_NUMERIC_VALUE",
        "INVALID_PUMP_STATE",
    ]

    def contains_critical_error(flags):
        if not flags:
            return False

        return any(
            flag in flags.split(";")
            for flag in critical_flags
        )

    rejected_mask = df["quality_flags"].apply(
        contains_critical_error
    )

    rejected = df.loc[rejected_mask].copy()
    valid = df.loc[~rejected_mask].copy()

    return valid, rejected


# ----------------------------------------------------------------
# Final schema
# ----------------------------------------------------------------

def prepare_clean_dataset(df):
    """
    Keep only the fields needed by downstream processes,
    plus useful normalized metadata.
    """

    columns = [
        "timestamp",
        "tag_name",
        "alarm_type",
        "severity",
        "value",
        "value_type",
        "status",
        "quality_flags",
    ]

    df = df[columns].copy()

    # Sort chronologically.
    df = df.sort_values(
        by="timestamp",
        ascending=True,
    )

    # Reset index.
    df = df.reset_index(drop=True)

    return df


# ----------------------------------------------------------------
# Quality report
# ----------------------------------------------------------------

def generate_quality_report(
    raw_df,
    cleaned_df,
    rejected_df,
    duplicates_df,
    quality_df,
):
    print()
    print("Generating quality report...")

    report_lines = []

    report_lines.append(
        "SCADA ALARM GATEWAY & MIGRATOR"
    )
    report_lines.append(
        "DATA QUALITY REPORT"
    )
    report_lines.append(
        "=" * 60
    )
    report_lines.append("")

    # Basic counts
    report_lines.append(
        f"Raw records: {len(raw_df):,}"
    )

    report_lines.append(
        f"Clean records: {len(cleaned_df):,}"
    )

    report_lines.append(
        f"Rejected records: {len(rejected_df):,}"
    )

    report_lines.append(
        f"Duplicate records removed: {len(duplicates_df):,}"
    )

    report_lines.append("")

    # Percentages
    total = len(raw_df)

    if total > 0:
        clean_pct = len(cleaned_df) / total * 100
        rejected_pct = len(rejected_df) / total * 100
        duplicate_pct = len(duplicates_df) / total * 100
    else:
        clean_pct = 0
        rejected_pct = 0
        duplicate_pct = 0

    report_lines.append(
        f"Clean percentage: {clean_pct:.2f}%"
    )

    report_lines.append(
        f"Rejected percentage: {rejected_pct:.2f}%"
    )

    report_lines.append(
        f"Duplicate percentage: {duplicate_pct:.2f}%"
    )

    report_lines.append("")

    # ------------------------------------------------------------
    # Rejection reasons
    # ------------------------------------------------------------

    report_lines.append(
        "QUALITY FLAGS"
    )
    report_lines.append(
        "-" * 60
    )

    if "quality_flags" in quality_df.columns:

        flag_counts = {}

        for flags in quality_df["quality_flags"].dropna():

            if not flags:
                continue

            for flag in str(flags).split(";"):

                if flag:
                    flag_counts[flag] = (
                        flag_counts.get(flag, 0) + 1
                    )

        if flag_counts:
            for flag, count in sorted(
                flag_counts.items(),
                key=lambda item: item[1],
                reverse=True,
            ):
                report_lines.append(
                    f"{flag}: {count:,}"
                )
        else:
            report_lines.append(
                "No quality issues detected."
            )

    report_lines.append("")

    # ------------------------------------------------------------
    # Tag distribution
    # ------------------------------------------------------------

    report_lines.append(
        "CLEAN DATA - TAG DISTRIBUTION"
    )
    report_lines.append(
        "-" * 60
    )

    if not cleaned_df.empty:
        for tag, count in (
            cleaned_df["tag_name"]
            .value_counts()
            .items()
        ):
            report_lines.append(
                f"{tag}: {count:,}"
            )

    report_lines.append("")

    # ------------------------------------------------------------
    # Severity distribution
    # ------------------------------------------------------------

    report_lines.append(
        "CLEAN DATA - SEVERITY DISTRIBUTION"
    )
    report_lines.append(
        "-" * 60
    )

    if not cleaned_df.empty:
        for severity, count in (
            cleaned_df["severity"]
            .value_counts()
            .items()
        ):
            report_lines.append(
                f"{severity}: {count:,}"
            )

    report_lines.append("")

    # ------------------------------------------------------------
    # Alarm distribution
    # ------------------------------------------------------------

    report_lines.append(
        "CLEAN DATA - ALARM DISTRIBUTION"
    )
    report_lines.append(
        "-" * 60
    )

    if not cleaned_df.empty:
        for alarm_type, count in (
            cleaned_df["alarm_type"]
            .value_counts()
            .items()
        ):
            report_lines.append(
                f"{alarm_type}: {count:,}"
            )

    report_lines.append("")

    report_lines.append(
        "NOTE:"
    )

    report_lines.append(
        "The raw dataset is intentionally imperfect and is "
        "preserved unchanged."
    )

    report_lines.append(
        "Rejected records are isolated for traceability."
    )

    report_lines.append(
        "Missing values are not automatically rejected because "
        "COMMUNICATION_LOST events legitimately contain NULL values."
    )

    QUALITY_REPORT_FILE.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )


# ----------------------------------------------------------------
# Main ETL process
# ----------------------------------------------------------------

def main():

    print("=" * 60)
    print("SCADA ALARM GATEWAY & MIGRATOR")
    print("DATA CLEANING AND NORMALIZATION")
    print("=" * 60)

    # 1. Load
    raw_df = load_raw_data()

    # 2. Validate structure
    validate_columns(raw_df)

    # 3. Clean
    processed_df = clean_data(raw_df)

    # Keep a copy with quality information for the report.
    quality_df = processed_df.copy()

    # 4. Detect duplicates
    processed_df, duplicates_df = detect_duplicates(
        processed_df
    )

    # 5. Separate rejected records
    clean_df, rejected_df = separate_rejected_records(
        processed_df
    )

    # 6. Prepare final clean dataset
    clean_df = prepare_clean_dataset(
        clean_df
    )

    # 7. Save clean dataset
    clean_df.to_csv(
        CLEAN_FILE,
        index=False,
        encoding="utf-8",
    )

    # 8. Save rejected records
    rejected_df.to_csv(
        REJECTED_FILE,
        index=False,
        encoding="utf-8",
    )

    # 9. Save duplicates
    duplicates_df.to_csv(
        DUPLICATES_FILE,
        index=False,
        encoding="utf-8",
    )

    # 10. Generate report
    generate_quality_report(
        raw_df=raw_df,
        cleaned_df=clean_df,
        rejected_df=rejected_df,
        duplicates_df=duplicates_df,
        quality_df=quality_df,
    )

    # ------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------

    print()
    print("=" * 60)
    print("ETL COMPLETED")
    print("=" * 60)

    print(
        f"Raw records:        {len(raw_df):,}"
    )

    print(
        f"Clean records:      {len(clean_df):,}"
    )

    print(
        f"Rejected records:   {len(rejected_df):,}"
    )

    print(
        f"Duplicates removed: {len(duplicates_df):,}"
    )

    print()
    print("Generated files:")
    print(f"  Clean:      {CLEAN_FILE}")
    print(f"  Rejected:   {REJECTED_FILE}")
    print(f"  Duplicates: {DUPLICATES_FILE}")
    print(f"  Report:     {QUALITY_REPORT_FILE}")

    print()
    print("Clean dataset preview:")
    print(
        clean_df.head(10).to_string(
            index=False
        )
    )

    print()
    print("Severity distribution:")
    print(
        clean_df["severity"]
        .value_counts()
        .to_string()
    )

    print()
    print("Tag distribution:")
    print(
        clean_df["tag_name"]
        .value_counts()
        .to_string()
    )


# ----------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------

if __name__ == "__main__":
    main()