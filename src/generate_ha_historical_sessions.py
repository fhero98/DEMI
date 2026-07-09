from pathlib import Path
import json
import re

import pandas as pd


# =========================================================
# Paths
# =========================================================
current_file_dir = Path(__file__).resolve().parent
project_root = current_file_dir.parent
raw_data_dir = project_root / "rawData"


# =========================================================
# Helpers
# =========================================================
def sanitize_ha_id_tag(value) -> str:
    if value is None or pd.isna(value):
        return "unknown"

    text = str(value).strip()

    if text.endswith(".0"):
        text = text[:-2]

    text = text.lower()
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")

    return text or "unknown"


def safe_value(row: dict, key: str, default=None):
    value = row.get(key, default)

    if pd.isna(value):
        return default

    return value


def normalize_float(value, default=0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default


def normalize_int(value, default=0) -> int:
    try:
        if value is None or pd.isna(value):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def make_session_id(row: dict) -> str:
    evse_id = safe_value(row, "evse_id", "unknown")
    start_date = safe_value(row, "start_date", "")

    return (
        f"B103-{evse_id}-"
        f"{str(start_date).replace(' ', '_').replace(':', '-').replace('/', '-')}"
    )


def yaml_single_quoted_json(data: dict) -> str:
    """
    Put JSON safely inside a YAML single-quoted string.
    If JSON contains single quotes, YAML needs them doubled.
    """
    text = json.dumps(data, ensure_ascii=False)
    return text.replace("'", "''")


# =========================================================
# Load and clean Excel data
# =========================================================
def load_clean_sessions() -> pd.DataFrame:
    path_b103_25 = raw_data_dir / "building103" / "sessionRepport_EN_31_12_2025_03_16_37_688.xlsx"
    path_b103_24 = raw_data_dir / "building103" / "sessionRepport_EN_31_12_2024_03_15_45_940.xlsx"
    path_b103_23 = raw_data_dir / "building103" / "sessionRepport_EN_31_12_2023_03_18_23_207.xlsx"

    df_b103_25 = pd.read_excel(path_b103_25, sheet_name=2)
    df_b103_24 = pd.read_excel(path_b103_24, sheet_name=2)
    df_b103_23 = pd.read_excel(path_b103_23, sheet_name=2)

    df = pd.concat(
        [df_b103_25, df_b103_24, df_b103_23],
        ignore_index=True
    )

    cols_to_drop = [
        "Unnamed: 0",
        "idle fee",
        "eMi3",
        "Location",
        "Zone",
        "SubOperator",
        "Evse",
        "charge amount",
        "CPO GROUP",
        "organisation",
        "EMSP",
        "EMSP CODE",
        "Valorization Incl. tax (EUR)",
        "Valorization Excl. tax (EUR)",
        "Payment type",
        "TVA/Siren",
        "Evse max power (kW)",
        "Notification Date",
    ]

    df = df.drop(
        columns=[c for c in cols_to_drop if c in df.columns],
        errors="ignore"
    )

    if "Evse Id" in df.columns:
        df["Evse Id"] = (
            df["Evse Id"]
            .astype(str)
            .str.extract(r"-(\d+)$")[0]
        )

    if "plug type" in df.columns:
        df["plug type"] = df["plug type"].replace({
            "T2S": "AC-Level2",
            "EF": "AC-Level1",
        })

    if "compliance" in df.columns:
        df["compliance"] = df["compliance"].replace({
            "valid": "ended",
            "invalid": "failed",
        })

    required_cols = [
        c for c in ["Evse Id", "plug type", "compliance", "idTag"]
        if c in df.columns
    ]

    if required_cols:
        df = df.dropna(subset=required_cols)

    rename_map = {
        "Evse Id": "evse_id",
        "plug type": "plug_type",
        "compliance": "session_status",

        "session start time": "start_date",
        "session end time": "end_date",
        "consumption (kWh)": "energy_kwh",
        "session duration": "duration",
        "charging duration": "charging_duration",

        "idTag": "id_tag",
        "Label RFID": "user_name",
        "max power (kW)": "max_power_kw",
    }

    df = df.rename(
        columns={k: v for k, v in rename_map.items() if k in df.columns}
    )

    if "id_tag" not in df.columns:
        raise ValueError("Column id_tag was not found after rename. Check Excel column idTag.")

    if "start_date" not in df.columns:
        raise ValueError("Column start_date was not found after rename. Check Excel column session start time.")

    df["start_date_dt"] = pd.to_datetime(df["start_date"], errors="coerce")

    if "end_date" in df.columns:
        df["end_date_dt"] = pd.to_datetime(df["end_date"], errors="coerce")
    else:
        df["end_date_dt"] = pd.NaT

    df = df.dropna(subset=["start_date_dt"])

    df["session_day"] = df["start_date_dt"].dt.date.astype(str)
    df["id_tag"] = df["id_tag"].astype(str).str.strip()
    df["id_tag_slug"] = df["id_tag"].apply(sanitize_ha_id_tag)

    rows = []

    for _, row in df.iterrows():
        row_dict = row.to_dict()
        session_id = make_session_id(row_dict)

        rows.append({
            "session_id": session_id,
            "vehicle_slug": row_dict.get("id_tag_slug", "unknown"),
            "vehicle_id": str(row_dict.get("id_tag", "unknown")),
            "session_day": str(row_dict.get("session_day", "unknown")),
            "status": str(row_dict.get("session_status", "unknown")),
            "start_date": str(row_dict.get("start_date", "")),
            "end_date": str(row_dict.get("end_date", "")),
            "energy_kwh": normalize_float(row_dict.get("energy_kwh")),
            "duration": normalize_int(row_dict.get("duration")),
            "charging_duration": normalize_int(row_dict.get("charging_duration")),
            "max_power_kw": normalize_float(row_dict.get("max_power_kw")),
            "evse_id": str(row_dict.get("evse_id", "unknown")),
            "plug_type": str(row_dict.get("plug_type", "unknown")),
            "user_name": str(row_dict.get("user_name", "")),
        })

    clean_df = pd.DataFrame(rows)

    clean_df = clean_df[
        (clean_df["vehicle_slug"] != "unknown") &
        (clean_df["session_id"].astype(str).str.len() > 0)
    ]

    clean_df = clean_df.drop_duplicates(subset=["session_id"])

    return clean_df.reset_index(drop=True)


# =========================================================
# Generate Historical Sessions Package
# =========================================================
def generate_home_assistant_historical_sessions_package() -> Path:
    df = load_clean_sessions()

    if df.empty:
        raise ValueError("No historical sessions found.")

    output_dir = current_file_dir / "ha_generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "ev_historical_sessions.yaml"

    vehicles = sorted(df["vehicle_slug"].dropna().unique().tolist())

    first_vehicle = vehicles[0]

    # Dates only for the first vehicle, so initial config is valid.
    first_vehicle_days = sorted(
        df.loc[df["vehicle_slug"] == first_vehicle, "session_day"]
        .dropna()
        .unique()
        .tolist()
    )

    if not first_vehicle_days:
        raise ValueError(f"No dates found for first vehicle: {first_vehicle}")

    first_day = first_vehicle_days[0]

    first_sessions_df = df[
        (df["vehicle_slug"] == first_vehicle) &
        (df["session_day"] == first_day)
    ]

    if first_sessions_df.empty:
        raise ValueError(f"No sessions found for first vehicle/day: {first_vehicle} / {first_day}")

    first_session = first_sessions_df.iloc[0]["session_id"]

    # Mapping: vehicle -> [dates]
    dates_by_vehicle = {}

    for _, row in df.iterrows():
        vehicle = row["vehicle_slug"]
        day = row["session_day"]

        dates_by_vehicle.setdefault(vehicle, set())
        dates_by_vehicle[vehicle].add(day)

    dates_by_vehicle = {
        vehicle: sorted(list(days_set))
        for vehicle, days_set in dates_by_vehicle.items()
    }

    # Mapping: vehicle|date -> [session_ids]
    sessions_by_vehicle_day = {}

    for _, row in df.iterrows():
        key = f"{row['vehicle_slug']}|{row['session_day']}"
        sessions_by_vehicle_day.setdefault(key, [])
        sessions_by_vehicle_day[key].append(row["session_id"])

    sessions_by_vehicle_day = {
        key: sorted(value)
        for key, value in sessions_by_vehicle_day.items()
    }

    # Mapping: session_id -> session details
    session_details = {}

    for _, row in df.iterrows():
        session_details[row["session_id"]] = {
            "vehicle_slug": row["vehicle_slug"],
            "vehicle_id": row["vehicle_id"],
            "session_day": row["session_day"],
            "status": row["status"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "energy_kwh": row["energy_kwh"],
            "duration": row["duration"],
            "charging_duration": row["charging_duration"],
            "max_power_kw": row["max_power_kw"],
            "evse_id": row["evse_id"],
            "plug_type": row["plug_type"],
            "user_name": row["user_name"],
        }

    dates_by_vehicle_json = yaml_single_quoted_json(dates_by_vehicle)
    sessions_by_vehicle_day_json = yaml_single_quoted_json(sessions_by_vehicle_day)
    session_details_json = yaml_single_quoted_json(session_details)

    lines = []
    lines.append("# Generated automatically from the EV Excel files")
    lines.append("# Copy this file to: /config/packages/ev_historical_sessions.yaml")
    lines.append("")

    # =====================================================
    # INPUT SELECTS
    # =====================================================
    lines.append("input_select:")

    lines.append("  ev_historical_vehicle:")
    lines.append("    name: EV Historical Vehicle")
    lines.append("    options:")
    for vehicle in vehicles:
        lines.append(f"      - \"{vehicle}\"")
    lines.append(f"    initial: \"{first_vehicle}\"")
    lines.append("")

    lines.append("  ev_historical_date:")
    lines.append("    name: EV Historical Date")
    lines.append("    options:")
    for day in first_vehicle_days:
        lines.append(f"      - \"{day}\"")
    lines.append(f"    initial: \"{first_day}\"")
    lines.append("")

    lines.append("  ev_historical_session:")
    lines.append("    name: EV Historical Session")
    lines.append("    options:")
    for session_id in sorted(first_sessions_df["session_id"].tolist()):
        lines.append(f"      - \"{session_id}\"")
    lines.append(f"    initial: \"{first_session}\"")
    lines.append("")

    # =====================================================
    # AUTOMATIONS
    # =====================================================
    lines.append("automation:")

    # Update date dropdown when vehicle changes
    lines.append("  - alias: EV Historical Update Date Options")
    lines.append("    trigger:")
    lines.append("      - platform: state")
    lines.append("        entity_id: input_select.ev_historical_vehicle")
    lines.append("    variables:")
    lines.append(f"      dates_map: '{dates_by_vehicle_json}'")
    lines.append("      selected_vehicle: \"{{ states('input_select.ev_historical_vehicle') }}\"")
    lines.append("      date_options: >")
    lines.append("        {{ (dates_map | from_json).get(selected_vehicle, ['no_dates_found']) }}")
    lines.append("      first_date: \"{{ date_options[0] }}\"")
    lines.append("    action:")
    lines.append("      - service: input_select.set_options")
    lines.append("        target:")
    lines.append("          entity_id: input_select.ev_historical_date")
    lines.append("        data:")
    lines.append("          options: \"{{ date_options }}\"")
    lines.append("")
    lines.append("      - service: input_select.select_option")
    lines.append("        target:")
    lines.append("          entity_id: input_select.ev_historical_date")
    lines.append("        data:")
    lines.append("          option: \"{{ first_date }}\"")
    lines.append("    mode: single")
    lines.append("")

    # Update session dropdown when vehicle or date changes
    lines.append("  - alias: EV Historical Update Session Options")
    lines.append("    trigger:")
    lines.append("      - platform: state")
    lines.append("        entity_id:")
    lines.append("          - input_select.ev_historical_vehicle")
    lines.append("          - input_select.ev_historical_date")
    lines.append("    variables:")
    lines.append(f"      sessions_map: '{sessions_by_vehicle_day_json}'")
    lines.append("      selected_key: \"{{ states('input_select.ev_historical_vehicle') ~ '|' ~ states('input_select.ev_historical_date') }}\"")
    lines.append("      session_options: >")
    lines.append("        {{ (sessions_map | from_json).get(selected_key, ['no_sessions_found']) }}")
    lines.append("      first_session: \"{{ session_options[0] }}\"")
    lines.append("    action:")
    lines.append("      - service: input_select.set_options")
    lines.append("        target:")
    lines.append("          entity_id: input_select.ev_historical_session")
    lines.append("        data:")
    lines.append("          options: \"{{ session_options }}\"")
    lines.append("")
    lines.append("      - service: input_select.select_option")
    lines.append("        target:")
    lines.append("          entity_id: input_select.ev_historical_session")
    lines.append("        data:")
    lines.append("          option: \"{{ first_session }}\"")
    lines.append("    mode: single")
    lines.append("")

    # =====================================================
    # TEMPLATE SENSORS
    # =====================================================
    lines.append("template:")
    lines.append("  - sensor:")

    def add_detail_sensor(
        name: str,
        unique_id: str,
        field: str,
        default: str = "unknown",
        unit: str | None = None
    ):
        lines.append(f"      - name: \"{name}\"")
        lines.append(f"        unique_id: {unique_id}")

        if unit:
            lines.append(f"        unit_of_measurement: \"{unit}\"")

        lines.append("        state: >")
        lines.append(f"          {{% set details = '{session_details_json}' | from_json %}}")
        lines.append("          {% set sid = states('input_select.ev_historical_session') %}")
        lines.append(f"          {{{{ details.get(sid, {{}}).get('{field}', '{default}') }}}}")
        lines.append("")

    add_detail_sensor("EV Historical Session Vehicle", "ev_historical_session_vehicle", "vehicle_id")
    add_detail_sensor("EV Historical Session Day", "ev_historical_session_day", "session_day")
    add_detail_sensor("EV Historical Session Status", "ev_historical_session_status", "status")
    add_detail_sensor("EV Historical Session Start Date", "ev_historical_session_start_date", "start_date")
    add_detail_sensor("EV Historical Session End Date", "ev_historical_session_end_date", "end_date")
    add_detail_sensor("EV Historical Session Energy", "ev_historical_session_energy", "energy_kwh", "0", "kWh")
    add_detail_sensor("EV Historical Session Duration", "ev_historical_session_duration", "duration", "0", "min")
    add_detail_sensor("EV Historical Session Charging Duration", "ev_historical_session_charging_duration", "charging_duration", "0", "min")
    add_detail_sensor("EV Historical Session Max Power", "ev_historical_session_max_power", "max_power_kw", "0", "kW")
    add_detail_sensor("EV Historical Session Charger", "ev_historical_session_charger", "evse_id")
    add_detail_sensor("EV Historical Session Plug Type", "ev_historical_session_plug_type", "plug_type")
    add_detail_sensor("EV Historical Session User Name", "ev_historical_session_user_name", "user_name")

    output_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Generated Home Assistant historical sessions package: {output_path}")
    print(f"Vehicles found: {len(vehicles)}")
    print(f"Days found for first vehicle: {len(first_vehicle_days)}")
    print(f"Sessions found: {len(df)}")
    print("First vehicle:", first_vehicle)
    print("First day:", first_day)
    print("First session:", first_session)

    return output_path


if __name__ == "__main__":
    generate_home_assistant_historical_sessions_package()