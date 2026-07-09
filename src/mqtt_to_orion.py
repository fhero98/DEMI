import json
import requests
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "ev/building103/charging_sessions"

ORION_LD = "http://127.0.0.1:1026/ngsi-ld/v1"

HEADERS_LD = {
    "Content-Type": "application/ld+json",
    "Accept": "application/ld+json",
}

CONTEXT = [
    "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    {
        "building": "https://example.org/ev#building",
        "evse_id": "https://example.org/ev#evseId",
        "plugType": "https://example.org/ev#plugType",
        "sessionStatus": "https://example.org/ev#sessionStatus",
        "startDate": "https://example.org/ev#startDate",
        "endDate": "https://example.org/ev#endDate",
        "energyKWh": "https://example.org/ev#energyKWh",
        "duration": "https://example.org/ev#duration",
        "chargingDuration": "https://example.org/ev#chargingDuration",
        "maxPowerKW": "https://example.org/ev#maxPowerKW",
        "idTag": "https://example.org/ev#idTag",
        "userName": "https://example.org/ev#userName",
        "connector": "https://example.org/ev#connector",
    },
]


def add_property_if_has_value(entity: dict, attr_name: str, value):
    if value is None:
        return

    if value == "":
        return

    entity[attr_name] = {
        "type": "Property",
        "value": value,
    }


def payload_to_entity(payload: dict) -> dict:
    session_id = payload["session_id"]

    entity = {
        "id": f"urn:ngsi-ld:ChargingSession:{session_id}",
        "type": "ChargingSession",
        "@context": CONTEXT,
    }

    add_property_if_has_value(entity, "building", payload.get("building"))
    add_property_if_has_value(entity, "evse_id", payload.get("evse_id"))
    add_property_if_has_value(entity, "plugType", payload.get("plug_type"))
    add_property_if_has_value(entity, "sessionStatus", payload.get("session_status"))
    add_property_if_has_value(entity, "startDate", payload.get("start_date"))
    add_property_if_has_value(entity, "endDate", payload.get("end_date"))
    add_property_if_has_value(entity, "energyKWh", payload.get("energy_kwh"))
    add_property_if_has_value(entity, "duration", payload.get("duration"))
    add_property_if_has_value(entity, "chargingDuration", payload.get("charging_duration"))
    add_property_if_has_value(entity, "maxPowerKW", payload.get("max_power_kw"))
    add_property_if_has_value(entity, "idTag", payload.get("id_tag"))
    add_property_if_has_value(entity, "userName", payload.get("user_name"))
    add_property_if_has_value(entity, "connector", payload.get("connector"))

    return entity


def create_entity(entity: dict):
    url = f"{ORION_LD}/entities"

    response = requests.post(
        url,
        headers=HEADERS_LD,
        json=entity,
        timeout=10,
    )

    print("CREATE STATUS:", response.status_code)
    print("CREATE RESPONSE:", response.text)

    return response


def update_entity_attrs(entity: dict):
    entity_id = entity["id"]
    url = f"{ORION_LD}/entities/{entity_id}/attrs"

    attrs_payload = dict(entity)
    attrs_payload.pop("id", None)
    attrs_payload.pop("type", None)

    response = requests.patch(
        url,
        headers=HEADERS_LD,
        json=attrs_payload,
        timeout=10,
    )

    print("UPDATE STATUS:", response.status_code)
    print("UPDATE RESPONSE:", response.text)

    return response


def upsert_entity(entity: dict):
    create_response = create_entity(entity)

    if create_response.status_code in (201, 204):
        print("CREATED:", entity["id"])
        return

    if create_response.status_code == 409:
        print("ENTITY EXISTS — GOING TO UPDATE")

        update_response = update_entity_attrs(entity)

        if update_response.status_code == 204:
            print("UPDATED:", entity["id"])
            return

        print("UPDATE ERROR:", update_response.status_code, update_response.text)
        return

    print("CREATE ERROR:", create_response.status_code, create_response.text)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code:", rc)
    client.subscribe(MQTT_TOPIC)
    print("Subscribed to:", MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        raw_payload = msg.payload.decode("utf-8")
        print("\nMQTT RAW:")
        print(raw_payload)

        payload = json.loads(raw_payload)

        if "session_id" not in payload:
            print("SKIP: payload has no session_id")
            return

        entity = payload_to_entity(payload)

        print("ENTITY ID:", entity["id"])
        upsert_entity(entity)

    except Exception as e:
        print("PROCESSING ERROR:", e)


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print("Connecting to MQTT broker...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    print("Listening for MQTT messages...")
    client.loop_forever()


if __name__ == "__main__":
    main()