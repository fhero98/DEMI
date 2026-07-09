import requests
from datetime import datetime, timezone

ORION = "http://127.0.0.1:1026"

CONTEXT = [
    "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    {
        "dateCreated": "https://example.org/ev#dateCreated",
        "refChargingStation": "https://example.org/ev#refChargingStation",
        "refChargingPoint": "https://example.org/ev#refChargingPoint",
        "operationalStatus": "https://example.org/ev#operationalStatus",
        "totalPoints": "https://example.org/ev#totalPoints",
        "availablePoints": "https://example.org/ev#availablePoints",
        "occupiedPoints": "https://example.org/ev#occupiedPoints",
        "faultedPoints": "https://example.org/ev#faultedPoints",
        "maintenancePoints": "https://example.org/ev#maintenancePoints",
        "reservedPoints": "https://example.org/ev#reservedPoints",
        "currentPowerConsumption": "https://example.org/ev#currentPowerConsumption",
        "activeSessionsCount": "https://example.org/ev#activeSessionsCount",
        "queueLength": "https://example.org/ev#queueLength",
        "estimatedWaitTime": "https://example.org/ev#estimatedWaitTime",
        "unitStatus": "https://example.org/ev#unitStatus",
        "operatingData": "https://example.org/ev#operatingData",
    }
]

HEADERS_LD = {
    "Content-Type": "application/ld+json",
    "Accept": "application/ld+json",
}


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def post_entity(payload: dict) -> None:
    r = requests.post(
        f"{ORION}/ngsi-ld/v1/entities",
        json=payload,
        headers=HEADERS_LD,
        timeout=10
    )
    if r.status_code in (201, 204, 409):
        return
    raise RuntimeError(f"POST entity failed: {r.status_code} {r.text}")


def charging_station_status(
    status_id: str,
    station_id: str,
    total_points: int,
    available_points: int,
    occupied_points: int,
    current_power_kw: float,
    active_sessions: int,
) -> dict:
    ts = now_iso()
    return {
        "@context": CONTEXT,
        "id": status_id,
        "type": "ChargingStationStatus",
        "refChargingStation": {
            "type": "Relationship",
            "object": station_id
        },
        "dateCreated": {
            "type": "Property",
            "value": {"@type": "DateTime", "@value": ts}
        },
        "operationalStatus": {
            "type": "Property",
            "value": "operational",
            "observedAt": ts
        },
        "totalPoints": {
            "type": "Property",
            "value": total_points,
            "observedAt": ts
        },
        "availablePoints": {
            "type": "Property",
            "value": available_points,
            "observedAt": ts
        },
        "occupiedPoints": {
            "type": "Property",
            "value": occupied_points,
            "observedAt": ts
        },
        "faultedPoints": {
            "type": "Property",
            "value": 0,
            "observedAt": ts
        },
        "maintenancePoints": {
            "type": "Property",
            "value": 0,
            "observedAt": ts
        },
        "reservedPoints": {
            "type": "Property",
            "value": 0,
            "observedAt": ts
        },
        "currentPowerConsumption": {
            "type": "Property",
            "value": current_power_kw,
            "observedAt": ts
        },
        "activeSessionsCount": {
            "type": "Property",
            "value": active_sessions,
            "observedAt": ts
        },
        "queueLength": {
            "type": "Property",
            "value": 0,
            "observedAt": ts
        },
        "estimatedWaitTime": {
            "type": "Property",
            "value": 0,
            "observedAt": ts
        },
    }


def charging_point_status(
    status_id: str,
    point_id: str,
    unit_status: str,
    current_power_kw: float,
    current_a: float,
    voltage_v: float,
) -> dict:
    ts = now_iso()
    return {
        "@context": CONTEXT,
        "id": status_id,
        "type": "ChargingPointStatus",
        "dateCreated": {
            "type": "Property",
            "value": {"@type": "DateTime", "@value": ts}
        },
        "refChargingPoint": {
            "type": "Relationship",
            "object": point_id
        },
        "unitStatus": {
            "type": "Property",
            "value": unit_status,
            "observedAt": ts
        },
        "operatingData": {
            "type": "Property",
            "value": {
                "currentPowerKW": current_power_kw,
                "currentA": current_a,
                "voltageV": voltage_v
            },
            "observedAt": ts
        }
    }


def main():
    # Stations already seeded in your other script
    S_RES = "urn:ngsi-ld:ChargingStation:ResidentialCS"
    S_OFF = "urn:ngsi-ld:ChargingStation:OfficeCS"

    # Station status entities
    station_statuses = [
        (
            "urn:ngsi-ld:ChargingStationStatus:ResidentialCS-Status",
            S_RES,
            2,   # totalPoints
            1,   # availablePoints
            1,   # occupiedPoints
            7.4, # currentPowerConsumption
            1    # activeSessionsCount
        ),
        (
            "urn:ngsi-ld:ChargingStationStatus:OfficeCS-Status",
            S_OFF,
            4,
            3,
            1,
            22.0,
            1
        ),
    ]

    for args in station_statuses:
        post_entity(charging_station_status(*args))

    print("[ok] ChargingStationStatus entities created/exist")

    # Point status entities
    point_statuses = [
        (
            "urn:ngsi-ld:ChargingPointStatus:Res-01-Status",
            "urn:ngsi-ld:ChargingPoint:Res-01",
            "charging",
            7.4,
            32.0,
            230.0
        ),
        (
            "urn:ngsi-ld:ChargingPointStatus:Res-02-Status",
            "urn:ngsi-ld:ChargingPoint:Res-02",
            "available",
            0.0,
            0.0,
            230.0
        ),
        (
            "urn:ngsi-ld:ChargingPointStatus:Off-01-Status",
            "urn:ngsi-ld:ChargingPoint:Off-01",
            "charging",
            22.0,
            32.0,
            400.0
        ),
        (
            "urn:ngsi-ld:ChargingPointStatus:Off-02-Status",
            "urn:ngsi-ld:ChargingPoint:Off-02",
            "available",
            0.0,
            0.0,
            400.0
        ),
        (
            "urn:ngsi-ld:ChargingPointStatus:Off-03-Status",
            "urn:ngsi-ld:ChargingPoint:Off-03",
            "available",
            0.0,
            0.0,
            400.0
        ),
        (
            "urn:ngsi-ld:ChargingPointStatus:Off-04-Status",
            "urn:ngsi-ld:ChargingPoint:Off-04",
            "available",
            0.0,
            0.0,
            400.0
        ),
    ]

    for args in point_statuses:
        post_entity(charging_point_status(*args))

    print("[ok] ChargingPointStatus entities created/exist")

    # Verify counts
    r1 = requests.get(
        f"{ORION}/ngsi-ld/v1/entities?type=ChargingStationStatus&limit=1000",
        headers=HEADERS_LD,
        timeout=10
    )
    r2 = requests.get(
        f"{ORION}/ngsi-ld/v1/entities?type=ChargingPointStatus&limit=1000",
        headers=HEADERS_LD,
        timeout=10
    )

    print(f"[verify] station status entities: {len(r1.json()) if r1.status_code == 200 else 'n/a'}")
    print(f"[verify] point status entities:   {len(r2.json()) if r2.status_code == 200 else 'n/a'}")


if __name__ == "__main__":
    main()