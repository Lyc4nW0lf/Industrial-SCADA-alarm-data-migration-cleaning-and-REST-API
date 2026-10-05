from pathlib import Path
import random
from datetime import datetime, timedelta

import pandas as pd

# ============================================================
# SCADA Alarm Gateway & Migrator
# Synthetic legacy dataset generator
# ============================================================

SEED = 42
N_RECORDS = 9_900

random.seed(SEED)

# Carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent

RAW_DIR = BASE_DIR / "data" / "raw"


RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RAW_DIR / "alarms_raw.csv"

# ----------------------------------------------------------------
# Tag configuration
# The ranges are fictional assumptions for the case study.
# ----------------------------------------------------------------

TAG_CONFIG = {
    "LT-101": {
        "description": "Tank level transmitter",
        "unit": "%",
        "normal_range": (40.0, 80.0),
        "alarm_low": 20.0,
        "alarm_high": 90.0,
        "normal_alarm_type": "NORMAL",
        "low_alarm_type": "LOW_LEVEL",
        "high_alarm_type": "HIGH_LEVEL",
    },
    "TT-101": {
        "description": "Tank temperature transmitter",
        "unit": "°C",
        "normal_range": (45.0, 75.0),
        "alarm_high": 85.0,
        "normal_alarm_type": "NORMAL",
        "high_alarm_type": "HIGH_TEMPERATURE",
    },
    "PT-101": {
        "description": "Process pressure transmitter",
        "unit": "bar",
        "normal_range": (4.0, 7.0),
        "alarm_low": 2.5,
        "alarm_high": 8.5,
        "normal_alarm_type": "NORMAL",
        "low_alarm_type": "LOW_PRESSURE",
        "high_alarm_type": "HIGH_PRESSURE",
    },
    "FT-101": {
        "description": "Process flow transmitter",
        "unit": "m3/h",
        "normal_range": (20.0, 40.0),
        "alarm_low": 10.0,
        "alarm_high": 50.0,
        "normal_alarm_type": "NORMAL",
        "low_alarm_type": "LOW_FLOW",
        "high_alarm_type": "HIGH_FLOW",
    },
    "P-101": {
        "description": "Main process pump",
        "unit": None,
        "device": True,
    },
    "P-102": {
        "description": "Secondary process pump",
        "unit": None,
        "device": True,
    },
    "V-101": {
        "description": "Control valve",
        "unit": "%",
        "device": True,
    },
    "M-101": {
        "description": "Main motor",
        "unit": "A",
        "normal_range": (0.0, 35.0),
        "alarm_high": 40.0,
        "normal_alarm_type": "NORMAL",
        "high_alarm_type": "HIGH_CURRENT",
    },
}

SEVERITY_BY_ALARM = {
    "NORMAL": "LOW",
    "LOW_LEVEL": "HIGH",
    "HIGH_LEVEL": "CRITICAL",
    "HIGH_TEMPERATURE": "HIGH",
    "LOW_PRESSURE": "MEDIUM",
    "HIGH_PRESSURE": "CRITICAL",
    "LOW_FLOW": "MEDIUM",
    "HIGH_FLOW": "HIGH",
    "PUMP_FAILURE": "CRITICAL",
    "COMMUNICATION_LOST": "MEDIUM",
    "VALVE_FAILURE": "HIGH",
    "HIGH_CURRENT": "HIGH",
    "MOTOR_FAILURE": "CRITICAL",
}

TAGS = list(TAG_CONFIG.keys())

# ----------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------

def random_timestamp(start, end):
    """Return a random datetime between start and end."""
    total_seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, total_seconds))


def random_normal_value(tag):
    config = TAG_CONFIG[tag]

    if tag in {"P-101", "P-102"}:
        return random.choice(["RUNNING", "RUNNING", "RUNNING", "STOPPED"])

    if tag == "V-101":
        return round(random.uniform(0, 100), 2)

    low, high = config["normal_range"]
    return round(random.uniform(low, high), 2)


def generate_sensor_event(tag):
    """Generate a coherent normal/alarm event for a sensor."""
    config = TAG_CONFIG[tag]
    roll = random.random()

    # ~92% normal process events
    if roll < 0.92:
        value = random_normal_value(tag)
        alarm_type = "NORMAL"
    else:
        # Generate an alarm coherently with the tag's limits.
        if tag == "LT-101":
            if random.random() < 0.5:
                value = round(random.uniform(5, 19.9), 2)
                alarm_type = "LOW_LEVEL"
            else:
                value = round(random.uniform(90.1, 99.9), 2)
                alarm_type = "HIGH_LEVEL"

        elif tag == "TT-101":
            value = round(random.uniform(85.1, 105.0), 2)
            alarm_type = "HIGH_TEMPERATURE"

        elif tag == "PT-101":
            if random.random() < 0.5:
                value = round(random.uniform(0.2, 2.49), 2)
                alarm_type = "LOW_PRESSURE"
            else:
                value = round(random.uniform(8.51, 10.0), 2)
                alarm_type = "HIGH_PRESSURE"

        elif tag == "FT-101":
            if random.random() < 0.5:
                value = round(random.uniform(1, 9.9), 2)
                alarm_type = "LOW_FLOW"
            else:
                value = round(random.uniform(50.1, 65.0), 2)
                alarm_type = "HIGH_FLOW"

        elif tag == "M-101":
            value = round(random.uniform(40.1, 60.0), 2)
            alarm_type = "HIGH_CURRENT"

        else:
            value = random_normal_value(tag)
            alarm_type = "NORMAL"

    severity = SEVERITY_BY_ALARM[alarm_type]
    status = "CLEARED" if alarm_type == "NORMAL" else random.choices(
        ["ACTIVE", "ACKNOWLEDGED", "CLEARED"],
        weights=[45, 20, 35],
        k=1,
    )[0]

    return {
        "timestamp": None,
        "tag_name": tag,
        "alarm_type": alarm_type,
        "severity": severity,
        "value": value,
        "status": status,
    }


def generate_pump_event(tag):
    """Generate coherent pump state/failure events."""
    roll = random.random()

    if roll < 0.94:
        value = random.choice(["RUNNING", "RUNNING", "RUNNING", "STOPPED"])
        alarm_type = "NORMAL"
    elif roll < 0.975:
        value = "STOPPED"
        alarm_type = "PUMP_FAILURE"
    else:
        value = None
        alarm_type = "COMMUNICATION_LOST"

    severity = SEVERITY_BY_ALARM[alarm_type]
    status = "CLEARED" if alarm_type == "NORMAL" else random.choices(
        ["ACTIVE", "ACKNOWLEDGED", "CLEARED"],
        weights=[45, 20, 35],
        k=1,
    )[0]

    return {
        "timestamp": None,
        "tag_name": tag,
        "alarm_type": alarm_type,
        "severity": severity,
        "value": value,
        "status": status,
    }


def generate_valve_event():
    roll = random.random()

    if roll < 0.95:
        value = round(random.uniform(0, 100), 2)
        alarm_type = "NORMAL"
    elif roll < 0.98:
        # Actual opening is far from expected command.
        value = round(random.uniform(0, 35), 2)
        alarm_type = "VALVE_FAILURE"
    else:
        value = None
        alarm_type = "COMMUNICATION_LOST"

    severity = SEVERITY_BY_ALARM[alarm_type]
    status = "CLEARED" if alarm_type == "NORMAL" else random.choices(
        ["ACTIVE", "ACKNOWLEDGED", "CLEARED"],
        weights=[45, 20, 35],
        k=1,
    )[0]

    return {
        "timestamp": None,
        "tag_name": "V-101",
        "alarm_type": alarm_type,
        "severity": severity,
        "value": value,
        "status": status,
    }


def generate_motor_event():
    return generate_sensor_event("M-101")


def generate_clean_event(tag):
    if tag in {"P-101", "P-102"}:
        return generate_pump_event(tag)
    if tag == "V-101":
        return generate_valve_event()
    return generate_sensor_event(tag)


# ----------------------------------------------------------------
# Legacy-data corruption
# These problems are intentional and will be handled by the ETL.
# ----------------------------------------------------------------

def corrupt_timestamp(value):
    return random.choice([
        value.strftime("%d/%m/%Y %H:%M:%S"),
        value.strftime("%Y-%m-%d %H:%M:%S"),
        value.strftime("%b %d, %Y %H:%M"),
        value.strftime("%Y/%m/%d %H:%M:%S"),
        value.strftime("%d-%m-%Y %H:%M"),
        "not-a-date",
        "32/15/2026 25:99:99",
        None,
    ])


def corrupt_tag(value):
    return random.choice([
        value.lower(),
        f" {value} ",
        value.replace("-", " "),
        value.replace("-", "_"),
        value,
    ])


def corrupt_severity(value):
    return random.choice([
        value.lower(),
        value.capitalize(),
        f" {value} ",
        value,
        "UNKNOWN",
        "potato",
        None,
    ])


def corrupt_status(value):
    return random.choice([
        value.lower(),
        value.capitalize(),
        f" {value} ",
        value,
        "UNKNOWN",
        None,
    ])


def corrupt_value(value):
    if value is None:
        return random.choice([None, "ERROR", "N/A", ""])

    if isinstance(value, (int, float)):
        return random.choice([
            str(value),
            f"{value:.1f}",
            value,
            "ERROR",
            "N/A",
            None,
        ])

    return random.choice([
        value,
        str(value),
        "ERROR",
        None,
    ])


def introduce_quality_issues(row):
    """
    Roughly 8% of records receive one or more intentional
    legacy-data quality problems.
    """
    if random.random() >= 0.08:
        return row

    number_of_errors = random.choices([1, 2, 3], weights=[65, 28, 7], k=1)[0]
    fields = random.sample(
        ["timestamp", "tag_name", "severity", "status", "value"],
        k=number_of_errors,
    )

    for field in fields:
        if field == "timestamp":
            row[field] = corrupt_timestamp(row[field])
        elif field == "tag_name":
            row[field] = corrupt_tag(row[field])
        elif field == "severity":
            row[field] = corrupt_severity(row[field])
        elif field == "status":
            row[field] = corrupt_status(row[field])
        elif field == "value":
            row[field] = corrupt_value(row[field])

    return row


# ----------------------------------------------------------------
# Dataset generation
# ----------------------------------------------------------------

def generate_dataset():
    start_date = datetime(2026, 9, 1, 0, 0, 0)
    end_date = datetime(2026, 9, 30, 23, 59, 59)

    rows = []

    # Weighted selection: process transmitters are more frequent.
    tag_weights = {
        "LT-101": 18,
        "TT-101": 15,
        "PT-101": 18,
        "FT-101": 15,
        "P-101": 12,
        "P-102": 8,
        "V-101": 7,
        "M-101": 7,
    }

    weighted_tags = list(tag_weights.keys())
    weights = list(tag_weights.values())

    for _ in range(N_RECORDS):
        tag = random.choices(weighted_tags, weights=weights, k=1)[0]
        row = generate_clean_event(tag)
        row["timestamp"] = random_timestamp(start_date, end_date)

        # Keep source data intentionally heterogeneous.
        row = introduce_quality_issues(row)

        rows.append(row)

    df = pd.DataFrame(rows)

    # Intentionally duplicate a small number of rows.
    duplicate_count = int(N_RECORDS * 0.01)
    duplicates = df.sample(
        n=duplicate_count,
        random_state=SEED
    ).copy()

    df = pd.concat([df, duplicates], ignore_index=True)

    # Shuffle so duplicates are not conveniently grouped.
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    return df


if __name__ == "__main__":
    df = generate_dataset()
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("=" * 60)
    print("SCADA synthetic dataset generated")
    print("=" * 60)
    print(f"Rows generated: {len(df):,}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    print("Columns:")
    print(", ".join(df.columns))
    print()
    print("Alarm distribution:")
    print(df["alarm_type"].value_counts(dropna=False).to_string())
    print()
    print("Severity distribution:")
    print(df["severity"].value_counts(dropna=False).to_string())
    print()
    print("Tag distribution:")
    print(df["tag_name"].value_counts(dropna=False).to_string())
    print()
    print("Preview:")
    print(df.head(10).to_string(index=False))