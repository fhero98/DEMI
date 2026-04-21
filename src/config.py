ORION_URL = "http://localhost:1026"

NGSI_LD_ENDPOINT = f"{ORION_URL}/ngsi-ld/v1/entities"
MINTAKA_URL = "http://localhost:8080"

headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/ld+json',
        'Link': '<https://raw.githubusercontent.com/chao0739/demi/refs/heads/main/contexts/datamodels.context-ngsi.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
    }


# headers = {
#         'Content-Type': 'application/json',
#         'Accept': 'application/json'
#         }

QL_URL = "http://localhost:8668"
#QL_NOTIFY = f"{QL_URL}/ngsi-ld/v1/notify"

QL_NOTIFY = "http://quantumleap:8668/v2/notify"

