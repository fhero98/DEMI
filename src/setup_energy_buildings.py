import requests
from datetime import datetime, timezone

ORION = "http://127.0.0.1:1026"

CONTEXT = [
    "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    {
        "name": "https://example.org/demi#name",
        "dateCreated": "https://example.org/demi#dateCreated",
        "energyConsumption": "https://example.org/energy#energyConsumption",
        "temperature": "https://example.org/energy#temperature",
        "gridStatus": "https://example.org/energy#gridStatus",
        "peakPower": "https://example.org/energy#peakPower",
    }
]

HEADERS_LD = {
    "Content-Type": "application/ld+json",
    "Accept": "application/ld+json",
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def post_entity(payload: dict):
    r = requests.post(f"{ORION}/ngsi-ld/v1/entities", json=payload, headers=HEADERS_LD, timeout=10)
    if r.status_code in (201, 204, 409):
        return
    raise RuntimeError(f"POST entity failed: {r.status_code} {r.text}")

def residential_building():
    return {
        "@context": CONTEXT,
        "id": "urn:ngsi-ld:Building:Residential",
        "type": "Building",
        "name": {"type": "Property", "value": "Residential Building"},
        "temperature": {"type": "Property", "value": 21.5, "observedAt": now_iso()},
        "energyConsumption": {"type": "Property", "value": 95.0, "observedAt": now_iso()},
        "gridStatus": {"type": "Property", "value": "connected", "observedAt": now_iso()},
        "peakPower": {"type": "Property", "value": 28.0},
        "dateCreated": {"type": "Property", "value": {"@type": "DateTime", "@value": now_iso()}}
    }

def office_building():
    return {
        "@context": CONTEXT,
        "id": "urn:ngsi-ld:Building:Office",
        "type": "Building",
        "name": {"type": "Property", "value": "Office Building"},
        "temperature": {"type": "Property", "value": 23.5, "observedAt": now_iso()},
        "energyConsumption": {"type": "Property", "value": 150.0, "observedAt": now_iso()},
        "gridStatus": {"type": "Property", "value": "connected", "observedAt": now_iso()},
        "peakPower": {"type": "Property", "value": 45.0},
        "dateCreated": {"type": "Property", "value": {"@type": "DateTime", "@value": now_iso()}}
    }

def main():
    r = requests.get(
        f"{ORION}/ngsi-ld/v1/entities?type=Building",
        headers=HEADERS_LD,
        timeout=10
    )

    if r.status_code == 200 and len(r.json()) >= 2:
        print("[ok] Buildings exist")
        return

    post_entity(residential_building())
    post_entity(office_building())

    r = requests.get(
        f"{ORION}/ngsi-ld/v1/entities?type=Building",
        headers=HEADERS_LD,
        timeout=10
    )

    print(r.json())

if __name__ == "__main__":
    main()