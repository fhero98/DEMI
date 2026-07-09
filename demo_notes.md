# DEMI Demo Architecture

---

## Infrastructure

- Orion Context Broker (NGSI-LD current state)
- MongoDB (current state storage)
- QuantumLeap (time-series ingestion)
- CrateDB (historical database)
- Grafana (visualization dashboard)

---

## JSON-LD Context

- Using `@context` inside payload (NGSI-LD core context)
- Custom energy namespace:
  - https://example.org/energy#
- Custom attributes mapped to IRIs:
  - refEnergyGrid
  - refPVSystem
  - refBatteryStorage
  - energyProduction
  - capacity
  - soc

Note:
In NGSI-LD every attribute must map to a URI via JSON-LD context.

---

## Buildings

### Residential Building
ID: urn:ngsi-ld:Building:Residential

Energy assets:
- Grid
- PV System (12 kW peak)
- No Battery

Relationships:
- refEnergyGrid → EnergyGrid:MainGrid
- refPVSystem → PVSystem:ResidentialPV

---

### Office Building
ID: urn:ngsi-ld:Building:Office

Energy assets:
- Grid
- Battery (40 kWh)
- No PV

Relationships:
- refEnergyGrid → EnergyGrid:MainGrid
- refBatteryStorage → BatteryStorage:OfficeBattery

---

## Energy Assets

### EnergyGrid
ID: urn:ngsi-ld:EnergyGrid:MainGrid

### PV System
ID: urn:ngsi-ld:PVSystem:ResidentialPV
- peakPower: 12 kW

### Battery Storage
ID: urn:ngsi-ld:BatteryStorage:OfficeBattery
- capacity: 40 kWh
- soc: 50% initial

---

## Relationships Model

Building
 ├── refEnergyGrid (1)
 ├── refPVSystem (0..1)
 ├── refBatteryStorage (0..1)
 └── refChargingStation(s) (0..*)

ChargingStation
 └── refBuilding (1)

ChargingPoint
 └── refChargingStation (1)

ChargingSession
 └── refChargingPoint (1)

---

## Orion Attribute Rules

- POST /entities → create entity
- POST /entities/{id}/attrs → add new attributes
- PATCH /entities/{id}/attrs → update existing attributes

---

## Data Flow

Python Script (simulation / updates)
        ↓
Orion (NGSI-LD current state)
        ↓ (subscription)
QuantumLeap
        ↓
CrateDB
        ↓
Grafana Dashboard

---

## Demo URLs

Orion version:
http://localhost:1026/version

All Buildings:
http://localhost:1026/ngsi-ld/v1/entities?type=Building

Residential:
http://localhost:1026/ngsi-ld/v1/entities/urn:ngsi-ld:Building:Residential

Office:
http://localhost:1026/ngsi-ld/v1/entities/urn:ngsi-ld:Building:Office
