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
# Generate Daily Home Assistant Package
# =========================================================
def generate_home_assistant_daily_summary_package() -> Path:
    vehicles = load_vehicle_ids_from_excel()

    output_dir = current_file_dir / "ha_generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "ev_daily_summary.yaml"

    lines = []
    lines.append("# Generated automatically from the EV Excel file")
    lines.append("# Copy this file to: /config/packages/ev_daily_summary.yaml")
    lines.append("")

    # =====================================================
    # COUNTERS
    # =====================================================
    lines.append("counter:")

    for vehicle in vehicles:
        slug = vehicle["slug"]
        raw_id = vehicle["raw_id"]

        lines.append(f"  ev_daily_completed_{slug}:")
        lines.append(f"    name: EV Daily Completed {raw_id}")
        lines.append("    initial: 0")
        lines.append("    step: 1")
        lines.append("")

        lines.append(f"  ev_daily_failed_{slug}:")
        lines.append(f"    name: EV Daily Failed {raw_id}")
        lines.append("    initial: 0")
        lines.append("    step: 1")
        lines.append("")

    # =====================================================
    # INPUT NUMBERS
    # =====================================================
    lines.append("input_number:")

    for vehicle in vehicles:
        slug = vehicle["slug"]
        raw_id = vehicle["raw_id"]

        lines.append(f"  ev_daily_energy_{slug}:")
        lines.append(f"    name: EV Daily Energy {raw_id}")
        lines.append("    min: 0")
        lines.append("    max: 100000")
        lines.append("    step: 0.01")
        lines.append("    unit_of_measurement: \"kWh\"")
        lines.append("")

        lines.append(f"  ev_daily_duration_{slug}:")
        lines.append(f"    name: EV Daily Duration {raw_id}")
        lines.append("    min: 0")
        lines.append("    max: 100000")
        lines.append("    step: 1")
        lines.append("    unit_of_measurement: \"min\"")
        lines.append("")

        lines.append(f"  ev_daily_max_power_{slug}:")
        lines.append(f"    name: EV Daily Max Power {raw_id}")
        lines.append("    min: 0")
        lines.append("    max: 1000")
        lines.append("    step: 0.01")
        lines.append("    unit_of_measurement: \"kW\"")
        lines.append("")

    # =====================================================
    # GROUP
    # =====================================================
    lines.append("group:")
    lines.append("  ev_daily_vehicle_completed_counters:")
    lines.append("    name: EV Daily Vehicle Completed Counters")
    lines.append("    entities:")

    for vehicle in vehicles:
        lines.append(f"      - counter.ev_daily_completed_{vehicle['slug']}")

    lines.append("")

    # =====================================================
    # AUTOMATIONS
    # =====================================================
    lines.append("automation:")

    # Update daily analytics
    lines.append("  - alias: EV Update Daily Analytics Per Vehicle")
    lines.append("    trigger:")
    lines.append("      - platform: mqtt")
    lines.append("        topic: ev/building103/charging_sessions")
    lines.append("    condition:")
    lines.append("      - condition: template")
    lines.append("        value_template: \"{{ trigger.payload_json.id_tag_slug is defined }}\"")
    lines.append("    variables:")
    lines.append("      vehicle_slug: \"{{ trigger.payload_json.id_tag_slug }}\"")
    lines.append("      session_status: \"{{ trigger.payload_json.session_status | default('unknown') }}\"")
    lines.append("      completed_counter: \"counter.ev_daily_completed_{{ vehicle_slug }}\"")
    lines.append("      failed_counter: \"counter.ev_daily_failed_{{ vehicle_slug }}\"")
    lines.append("      energy_entity: \"input_number.ev_daily_energy_{{ vehicle_slug }}\"")
    lines.append("      duration_entity: \"input_number.ev_daily_duration_{{ vehicle_slug }}\"")
    lines.append("      max_power_entity: \"input_number.ev_daily_max_power_{{ vehicle_slug }}\"")
    lines.append("      energy_value: \"{{ trigger.payload_json.energy_kwh | default(0) | float(0) }}\"")
    lines.append("      duration_value: \"{{ trigger.payload_json.duration | default(0) | float(0) }}\"")
    lines.append("      power_value: \"{{ trigger.payload_json.max_power_kw | default(0) | float(0) }}\"")
    lines.append("    action:")
    lines.append("      - choose:")
    lines.append("          - conditions:")
    lines.append("              - condition: template")
    lines.append("                value_template: \"{{ session_status == 'ended' and states(completed_counter) not in ['unknown', 'unavailable'] }}\"")
    lines.append("            sequence:")
    lines.append("              - service: counter.increment")
    lines.append("                data:")
    lines.append("                  entity_id: \"{{ completed_counter }}\"")
    lines.append("")
    lines.append("              - service: input_number.set_value")
    lines.append("                data:")
    lines.append("                  entity_id: \"{{ energy_entity }}\"")
    lines.append("                  value: \"{{ states(energy_entity) | float(0) + energy_value }}\"")
    lines.append("")
    lines.append("              - service: input_number.set_value")
    lines.append("                data:")
    lines.append("                  entity_id: \"{{ duration_entity }}\"")
    lines.append("                  value: \"{{ states(duration_entity) | float(0) + duration_value }}\"")
    lines.append("")
    lines.append("              - choose:")
    lines.append("                  - conditions:")
    lines.append("                      - condition: template")
    lines.append("                        value_template: \"{{ power_value > (states(max_power_entity) | float(0)) }}\"")
    lines.append("                    sequence:")
    lines.append("                      - service: input_number.set_value")
    lines.append("                        data:")
    lines.append("                          entity_id: \"{{ max_power_entity }}\"")
    lines.append("                          value: \"{{ power_value }}\"")
    lines.append("")
    lines.append("          - conditions:")
    lines.append("              - condition: template")
    lines.append("                value_template: \"{{ session_status == 'failed' and states(failed_counter) not in ['unknown', 'unavailable'] }}\"")
    lines.append("            sequence:")
    lines.append("              - service: counter.increment")
    lines.append("                data:")
    lines.append("                  entity_id: \"{{ failed_counter }}\"")
    lines.append("    mode: queued")
    lines.append("")

    # Daily notification
    lines.append("  - alias: EV Daily Charging Summary For All Vehicles")
    lines.append("    trigger:")
    lines.append("      - platform: time")
    lines.append("        at: \"21:00:00\"")
    lines.append("    action:")
    lines.append("      - repeat:")
    lines.append("          for_each: \"{{ expand('group.ev_daily_vehicle_completed_counters') | map(attribute='entity_id') | list }}\"")
    lines.append("          sequence:")
    lines.append("            - variables:")
    lines.append("                slug: \"{{ repeat.item | replace('counter.ev_daily_completed_', '') }}\"")
    lines.append("                vehicle_name: \"{{ state_attr(repeat.item, 'friendly_name') | replace('EV Daily Completed ', '') }}\"")
    lines.append("                completed: \"{{ states('counter.ev_daily_completed_' ~ slug) }}\"")
    lines.append("                failed: \"{{ states('counter.ev_daily_failed_' ~ slug) }}\"")
    lines.append("                energy: \"{{ states('input_number.ev_daily_energy_' ~ slug) }}\"")
    lines.append("                duration: \"{{ states('input_number.ev_daily_duration_' ~ slug) }}\"")
    lines.append("                max_power: \"{{ states('input_number.ev_daily_max_power_' ~ slug) }}\"")
    lines.append("")
    lines.append("            - service: notify.mobile_app_fotis_device")
    lines.append("              data:")
    lines.append("                title: \"EV Daily Summary {{ vehicle_name }}\"")
    lines.append("                message: >")
    lines.append("                  Completed sessions today: {{ completed }}")
    lines.append("                  Failed sessions today: {{ failed }}")
    lines.append("                  Total energy today: {{ energy }} kWh")
    lines.append("                  Total duration today: {{ duration }} min")
    lines.append("                  Max power today: {{ max_power }} kW")
    lines.append("                data:")
    lines.append("                  tag: \"daily_summary_{{ slug }}\"")
    lines.append("                  group: \"daily_summary_{{ slug }}\"")
    lines.append("                  channel: \"EV Daily Summary\"")
    lines.append("")
    lines.append("            - delay:")
    lines.append("                seconds: 2")
    lines.append("")

    # Reset daily helpers
    lines.append("      - repeat:")
    lines.append("          for_each: \"{{ expand('group.ev_daily_vehicle_completed_counters') | map(attribute='entity_id') | list }}\"")
    lines.append("          sequence:")
    lines.append("            - variables:")
    lines.append("                slug: \"{{ repeat.item | replace('counter.ev_daily_completed_', '') }}\"")
    lines.append("")
    lines.append("            - service: counter.reset")
    lines.append("              data:")
    lines.append("                entity_id: \"{{ 'counter.ev_daily_completed_' ~ slug }}\"")
    lines.append("")
    lines.append("            - service: counter.reset")
    lines.append("              data:")
    lines.append("                entity_id: \"{{ 'counter.ev_daily_failed_' ~ slug }}\"")
    lines.append("")
    lines.append("            - service: input_number.set_value")
    lines.append("              data:")
    lines.append("                entity_id: \"{{ 'input_number.ev_daily_energy_' ~ slug }}\"")
    lines.append("                value: 0")
    lines.append("")
    lines.append("            - service: input_number.set_value")
    lines.append("              data:")
    lines.append("                entity_id: \"{{ 'input_number.ev_daily_duration_' ~ slug }}\"")
    lines.append("                value: 0")
    lines.append("")
    lines.append("            - service: input_number.set_value")
    lines.append("              data:")
    lines.append("                entity_id: \"{{ 'input_number.ev_daily_max_power_' ~ slug }}\"")
    lines.append("                value: 0")
    lines.append("    mode: single")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Generated Home Assistant daily package: {output_path}")
    print(f"Vehicles found: {len(vehicles)}")

    return output_path


if __name__ == "__main__":
    generate_home_assistant_daily_summary_package()