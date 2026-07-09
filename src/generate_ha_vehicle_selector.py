from pathlib import Path
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


def load_vehicle_ids_from_excel() -> list[dict]:
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

    if "idTag" not in df.columns:
        raise ValueError("Column 'idTag' was not found in the Excel files.")

    vehicles = []
    seen_slugs = set()

    for value in df["idTag"].dropna().tolist():
        raw_id = str(value).strip()

        if raw_id.endswith(".0"):
            raw_id = raw_id[:-2]

        slug = sanitize_ha_id_tag(raw_id)

        if slug == "unknown" or slug in seen_slugs:
            continue

        seen_slugs.add(slug)
        vehicles.append({
            "raw_id": raw_id,
            "slug": slug,
        })

    return sorted(vehicles, key=lambda item: item["slug"])


# =========================================================
# Generate Vehicle Selector Package
# =========================================================
def generate_home_assistant_vehicle_selector_package() -> Path:
    vehicles = load_vehicle_ids_from_excel()

    if not vehicles:
        raise ValueError("No vehicles were found from Excel idTag column.")

    output_dir = current_file_dir / "ha_generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "ev_vehicle_selector.yaml"

    initial_vehicle = vehicles[0]["slug"]

    lines = []
    lines.append("# Generated automatically from the EV Excel file")
    lines.append("# Copy this file to: /config/packages/ev_vehicle_selector.yaml")
    lines.append("")

    # =====================================================
    # INPUT SELECT
    # =====================================================
    lines.append("input_select:")
    lines.append("  ev_selected_vehicle:")
    lines.append("    name: EV Selected Vehicle")
    lines.append("    options:")

    for vehicle in vehicles:
        lines.append(f"      - \"{vehicle['slug']}\"")

    lines.append(f"    initial: \"{initial_vehicle}\"")
    lines.append("")

    # =====================================================
    # TEMPLATE SENSORS
    # =====================================================
    lines.append("template:")
    lines.append("  - sensor:")

    lines.append("      - name: \"EV Selected Vehicle ID\"")
    lines.append("        unique_id: ev_selected_vehicle_id")
    lines.append("        state: \"{{ states('input_select.ev_selected_vehicle') }}\"")
    lines.append("")

    # Daily
    lines.append("      - name: \"EV Selected Daily Completed\"")
    lines.append("        unique_id: ev_selected_daily_completed")
    lines.append("        state: >")
    lines.append("          {{ states('counter.ev_daily_completed_' ~ states('input_select.ev_selected_vehicle')) | int(0) }}")
    lines.append("")

    lines.append("      - name: \"EV Selected Daily Failed\"")
    lines.append("        unique_id: ev_selected_daily_failed")
    lines.append("        state: >")
    lines.append("          {{ states('counter.ev_daily_failed_' ~ states('input_select.ev_selected_vehicle')) | int(0) }}")
    lines.append("")

    lines.append("      - name: \"EV Selected Daily Energy\"")
    lines.append("        unique_id: ev_selected_daily_energy")
    lines.append("        unit_of_measurement: \"kWh\"")
    lines.append("        state: >")
    lines.append("          {{ states('input_number.ev_daily_energy_' ~ states('input_select.ev_selected_vehicle')) | float(0) }}")
    lines.append("")

    lines.append("      - name: \"EV Selected Daily Duration\"")
    lines.append("        unique_id: ev_selected_daily_duration")
    lines.append("        unit_of_measurement: \"min\"")
    lines.append("        state: >")
    lines.append("          {{ states('input_number.ev_daily_duration_' ~ states('input_select.ev_selected_vehicle')) | float(0) }}")
    lines.append("")

    lines.append("      - name: \"EV Selected Daily Max Power\"")
    lines.append("        unique_id: ev_selected_daily_max_power")
    lines.append("        unit_of_measurement: \"kW\"")
    lines.append("        state: >")
    lines.append("          {{ states('input_number.ev_daily_max_power_' ~ states('input_select.ev_selected_vehicle')) | float(0) }}")
    lines.append("")

    # Weekly
    lines.append("      - name: \"EV Selected Weekly Completed\"")
    lines.append("        unique_id: ev_selected_weekly_completed")
    lines.append("        state: >")
    lines.append("          {{ states('counter.ev_weekly_completed_' ~ states('input_select.ev_selected_vehicle')) | int(0) }}")
    lines.append("")

    lines.append("      - name: \"EV Selected Weekly Failed\"")
    lines.append("        unique_id: ev_selected_weekly_failed")
    lines.append("        state: >")
    lines.append("          {{ states('counter.ev_weekly_failed_' ~ states('input_select.ev_selected_vehicle')) | int(0) }}")
    lines.append("")

    lines.append("      - name: \"EV Selected Weekly Energy\"")
    lines.append("        unique_id: ev_selected_weekly_energy")
    lines.append("        unit_of_measurement: \"kWh\"")
    lines.append("        state: >")
    lines.append("          {{ states('input_number.ev_weekly_energy_' ~ states('input_select.ev_selected_vehicle')) | float(0) }}")
    lines.append("")

    lines.append("      - name: \"EV Selected Weekly Duration\"")
    lines.append("        unique_id: ev_selected_weekly_duration")
    lines.append("        unit_of_measurement: \"min\"")
    lines.append("        state: >")
    lines.append("          {{ states('input_number.ev_weekly_duration_' ~ states('input_select.ev_selected_vehicle')) | float(0) }}")
    lines.append("")

    lines.append("      - name: \"EV Selected Weekly Max Power\"")
    lines.append("        unique_id: ev_selected_weekly_max_power")
    lines.append("        unit_of_measurement: \"kW\"")
    lines.append("        state: >")
    lines.append("          {{ states('input_number.ev_weekly_max_power_' ~ states('input_select.ev_selected_vehicle')) | float(0) }}")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Generated Home Assistant vehicle selector package: {output_path}")
    print(f"Vehicles found: {len(vehicles)}")
    print("First vehicle:", initial_vehicle)

    return output_path


if __name__ == "__main__":
    generate_home_assistant_vehicle_selector_package()