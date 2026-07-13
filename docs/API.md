# REST API Reference

Base URL: `http://localhost:5000` (when running `python3 backend/api.py`).
All request/response bodies are JSON.

## Health

`GET /api/health`
```json
{ "status": "ok" }
```

## Status

`GET /api/status` — full live snapshot: slots, currently parked, waiting queue.
```json
{
  "slots": [ { "slot_id": 1, "slot_number": "A1", "slot_type": "General", "status": "Empty" }, ... ],
  "parked": [ { "record_id": 1, "vehicle_number": "PB08AB1234", "slot_number": "A1", "entry_time": "..." } ],
  "waiting": [ { "vehicle_number": "...", "owner_name": "...", "vehicle_type": "...", "requested_time": "..." } ],
  "parked_count": 1,
  "waiting_count": 0
}
```

`PATCH /api/slots/<slot_number>` — admin override, body `{ "status": "OutOfService" | "Empty" }`.
- `400` if status isn't one of the two allowed values.
- `404` if the slot doesn't exist.
- `409` if the slot is currently `Occupied` (can't override an occupied slot).

## Vehicle Entry

`POST /api/entry`
```json
{ "vehicle_number": "PB08AB1234", "owner_name": "Aman Sharma", "vehicle_type": "Car" }
```
Response (`200`):
```json
{ "status": "PARKED", "message": "Vehicle parked in slot A1.", "slot_number": "A1", "queue_position": 0 }
```
or, if the lot is full:
```json
{ "status": "QUEUED", "message": "Lot is full. Added to waiting queue at position 1.", "slot_number": "", "queue_position": 1 }
```
`400` if `vehicle_number`/`owner_name`/`vehicle_type` fail validation (see `backend/validation.py`).
`409` if the vehicle is already parked.

## Vehicle Exit

`POST /api/exit`
```json
{ "vehicle_number": "PB08AB1234" }
```
Response (`200`):
```json
{
  "status": "SUCCESS",
  "message": "Vehicle exited. Amount due: Rs 20.00",
  "amount": 20.0,
  "slot_freed_number": "A1",
  "promoted_vehicle_number": "CAR007"
}
```
`promoted_vehicle_number` is `""` unless a waiting vehicle was auto-promoted into the freed slot.
`404` if the vehicle isn't currently parked. `400` on invalid vehicle number.

## Search Vehicle

`GET /api/search/<vehicle_number>`
```json
{
  "found": true,
  "vehicle": { "vehicle_id": 1, "vehicle_number": "PB08AB1234", "owner_name": "...", "vehicle_type": "Car" },
  "currently_parked": true,
  "slot_number": "A1",
  "entry_time": "2026-07-09 04:50:03"
}
```
`404` with `{ "found": false }` if unknown.

## History

`GET /api/history?limit=50` — most recent actions first (in-memory session log).
```json
[ { "action_type": "EXIT", "vehicle_number": "...", "slot_number": "A1", "timestamp": "...", "amount": 20.0 }, ... ]
```

## Reports

`GET /api/report` — persisted revenue/occupancy summary (requires the real database; `501` on the mock store).
```json
{
  "total_revenue": 340.0,
  "vehicles_serviced": 12,
  "revenue_by_type": { "Car": 240.0, "Bike": 60.0, "Truck": 40.0 },
  "slot_occupancy": { "total": 10, "occupied": 4, "empty": 5, "out_of_service": 1 },
  "recent_transactions": [ { "vehicle_number": "...", "vehicle_type": "...", "slot_number": "...", "entry_time": "...", "exit_time": "...", "amount": 20.0 } ]
}
```

## Admin Login

`POST /api/admin/login`
```json
{ "username": "admin", "password": "..." }
```
`200` with `{ "status": "ok", "username": "admin" }` on success, `401` on bad credentials.
Requires the real database (`501` on the mock store — there's no admin table to check).

---

## Running against the mock store (no database)

```bash
python3 backend/api.py --mock
```
Every endpoint above works except `/api/report` and `/api/admin/login`, which need
the real PostgreSQL-backed tables. Data resets whenever the process restarts.
