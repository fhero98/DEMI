import requests
import time
import sys
from datetime import datetime, timezone, timedelta

ORION = "http://127.0.0.1:1026"
HEADERS = {
    "Content-Type": "application/ld+json",
    "Accept": "application/ld+json"
}

SESSION_IDS = [
    "urn:ngsi-ld:ChargingSession:Res-01-Session-1",
    "urn:ngsi-ld:ChargingSession:Off-01-Session-1",
]

POWER_BY_SESSION = {
    "urn:ngsi-ld:ChargingSession:Res-01-Session-1": 7.4,
    "urn:ngsi-ld:ChargingSession:Off-01-Session-1": 22.0,
}

base = datetime.now(timezone.utc)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 5

for i in range(n):
    ts = (base + timedelta(seconds=i * 15)).isoformat().replace("+00:00", "Z")

    for session_id in SESSION_IDS:
        if session_id == "urn:ngsi-ld:ChargingSession:Res-01-Session-1":
            energy_value = float(i + 1)
        else:
            energy_value = round((i + 1) * 1.8, 2)

        payload = {
            "@context": [
                "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
                {
                    "energyDelivered": "https://example.org/ev#energyDelivered",
                    "averageChargingPower": "https://example.org/ev#averageChargingPower",
                    "sessionStatus": "https://example.org/ev#sessionStatus"
                }
            ],
            "https://example.org/ev#energyDelivered": {
                "type": "Property",
                "value": energy_value,
                "observedAt": ts
            },
            "https://example.org/ev#averageChargingPower": {
                "type": "Property",
                "value": POWER_BY_SESSION[session_id],
                "observedAt": ts
            },
            "https://example.org/ev#sessionStatus": {
                "type": "Property",
                "value": "charging",
                "observedAt": ts
            }
        }

        r = requests.patch(
            f"{ORION}/ngsi-ld/v1/entities/{session_id}/attrs",
            json=payload,
            headers=HEADERS,
            timeout=10
        )

        print(
            f"{session_id} | energyDelivered={energy_value} | "
            f"averageChargingPower={POWER_BY_SESSION[session_id]} | {r.status_code}"
        )

        if r.status_code >= 300:
            print(r.text)

    time.sleep(1)