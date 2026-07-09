import requests
from datetime import datetime, timezone

ORION = "http://127.0.0.1:1026"

CONTEXT = [
    "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    {
        "stationName": "https://example.org/ev#stationName",
        "dateCreated": "https://example.org/ev#dateCreated",
        "lastUpdated": "https://example.org/ev#lastUpdated",
        "refBuilding": "https://example.org/ev#refBuilding",
        "refChargingStation": "https://example.org/ev#refChargingStation",
        "refChargingPoint": "https://example.org/ev#refChargingPoint",
        "totalChargingPoints": "https://example.org/ev#totalChargingPoints",
        "chargingType": "https://example.org/ev#chargingType",
        "connectorTypes": "https://example.org/ev#connectorTypes",
        "numberOfConnectors": "https://example.org/ev#numberOfConnectors",
        "sessionStatus": "https://example.org/ev#sessionStatus",
        "sessionStartTime": "https://example.org/ev#sessionStartTime",
        "energyDelivered": "https://example.org/ev#energyDelivered",
        "averageChargingPower": "https://example.org/ev#averageChargingPower",
        "maxChargingPower": "https://example.org/ev#maxChargingPower",
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


def charging_station(station_id: str, name: str, building_id: str, total_points: int) -> dict:
    ts = now_iso()
    return {
        "@context": CONTEXT,
        "id": station_id,
        "type": "ChargingStation",
        "stationName": {"type": "Property", "value": name},
        "refBuilding": {"type": "Relationship", "object": building_id},
        "totalChargingPoints": {"type": "Property", "value": total_points},
        "dateCreated": {
            "type": "Property",
            "value": {"@type": "DateTime", "@value": ts}
        },
        "lastUpdated": {
            "type": "Property",
            "value": {"@type": "DateTime", "@value": ts}
        },
    }


def charging_point(point_id: str, station_id: str, max_power_kw: float, connector: str) -> dict:
    ts = now_iso()

    charging_type = "AC-Level2" if max_power_kw <= 7.4 else "DC-FastCharging"

    return {
        "@context": CONTEXT,
        "id": point_id,
        "type": "ChargingPoint",
        "refChargingStation": {"type": "Relationship", "object": station_id},
        "chargingType": {"type": "Property", "value": charging_type},
        "connectorTypes": {"type": "Property", "value": connector},
        "numberOfConnectors": {"type": "Property", "value": 1},
        "dateCreated": {
            "type": "Property",
            "value": {"@type": "DateTime", "@value": ts}
        },
        "lastUpdated": {
            "type": "Property",
            "value": {"@type": "DateTime", "@value": ts}
        },
    }



def main():
    # Buildings
    B_RES = "urn:ngsi-ld:Building:Residential"
    B_OFF = "urn:ngsi-ld:Building:Office"

    # Stations
    S_RES = "urn:ngsi-ld:ChargingStation:ResidentialCS"
    S_OFF = "urn:ngsi-ld:ChargingStation:OfficeCS"

    # 1) ChargingStations
    post_entity(charging_station(S_RES, "Residential Charging Station", B_RES, 2))
    post_entity(charging_station(S_OFF, "Office Charging Station", B_OFF, 4))
    print("[ok] ChargingStations created/exist")

    # 2) ChargingPoints
    res_points = [
        ("urn:ngsi-ld:ChargingPoint:Res-01", S_RES, 7.4, "Type2"),
        ("urn:ngsi-ld:ChargingPoint:Res-02", S_RES, 7.4, "Type2"),
    ]

    off_points = [
        ("urn:ngsi-ld:ChargingPoint:Off-01", S_OFF, 22.0, "Type2"),
        ("urn:ngsi-ld:ChargingPoint:Off-02", S_OFF, 22.0, "Type2"),
        ("urn:ngsi-ld:ChargingPoint:Off-03", S_OFF, 11.0, "Type2"),
        ("urn:ngsi-ld:ChargingPoint:Off-04", S_OFF, 11.0, "Type2"),
    ]

    for pid, sid, pwr, conn in res_points + off_points:
        post_entity(charging_point(pid, sid, pwr, conn))

    print("[ok] ChargingPoints created/exist")



if __name__ == "__main__":
    main()