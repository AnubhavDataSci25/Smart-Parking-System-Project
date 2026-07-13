-- =====================================================================
-- Smart Parking Management System - Database Schema
-- Engine: PostgreSQL (13+)
-- =====================================================================
-- Usage:
--   createdb smart_parking
--   psql -d smart_parking -f database/schema.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- Table: vehicles
-- One row per distinct vehicle that has ever entered the lot.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id      SERIAL PRIMARY KEY,
    vehicle_number  VARCHAR(20) NOT NULL UNIQUE,   -- e.g. "PB08AB1234"
    owner_name      VARCHAR(100) NOT NULL,
    vehicle_type    VARCHAR(10) NOT NULL CHECK (vehicle_type IN ('Car', 'Bike', 'Truck', 'Other')),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- Table: parking_slots
-- Fixed set of physical slots in the lot.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parking_slots (
    slot_id      SERIAL PRIMARY KEY,
    slot_number  VARCHAR(10) NOT NULL UNIQUE,       -- e.g. "A1", "A2"
    slot_type    VARCHAR(10) NOT NULL DEFAULT 'General' CHECK (slot_type IN ('General', 'Bike', 'Handicap', 'EV')),
    status       VARCHAR(15) NOT NULL DEFAULT 'Empty' CHECK (status IN ('Empty', 'Occupied', 'Reserved', 'OutOfService'))
);

-- ---------------------------------------------------------------------
-- Table: parking_records
-- One row per entry/exit event. exit_time & amount are NULL while
-- the vehicle is still parked.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parking_records (
    record_id    SERIAL PRIMARY KEY,
    vehicle_id   INTEGER NOT NULL REFERENCES vehicles(vehicle_id),
    slot_id      INTEGER NOT NULL REFERENCES parking_slots(slot_id),
    entry_time   TIMESTAMP NOT NULL DEFAULT NOW(),
    exit_time    TIMESTAMP,
    amount       NUMERIC(10, 2),
    CHECK (exit_time IS NULL OR exit_time >= entry_time)
);

-- ---------------------------------------------------------------------
-- Table: admins
-- NOTE: password_hash stores a SHA-256 (or bcrypt) hash, never plaintext.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    admin_id       SERIAL PRIMARY KEY,
    username       VARCHAR(50) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL
);

-- ---------------------------------------------------------------------
-- Indexes for fast lookups (hash-map-style search by reg. number,
-- and quick "who is currently parked" queries)
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_vehicles_number   ON vehicles(vehicle_number);
CREATE INDEX IF NOT EXISTS idx_records_open_exit ON parking_records(exit_time);
CREATE INDEX IF NOT EXISTS idx_records_vehicle    ON parking_records(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_slots_status       ON parking_slots(status);

-- ---------------------------------------------------------------------
-- Seed data: 10 parking slots (6 General, 2 Bike, 1 Handicap, 1 EV)
-- and 1 default admin.
-- Default admin login -> username: admin / password: (set on first run)
-- ---------------------------------------------------------------------
INSERT INTO parking_slots (slot_number, slot_type, status) VALUES
    ('A1', 'General', 'Empty'),
    ('A2', 'General', 'Empty'),
    ('A3', 'General', 'Empty'),
    ('A4', 'General', 'Empty'),
    ('A5', 'General', 'Empty'),
    ('A6', 'General', 'Empty'),
    ('B1', 'Bike',    'Empty'),
    ('B2', 'Bike',    'Empty'),
    ('C1', 'Handicap','Empty'),
    ('C2', 'EV',      'Empty')
ON CONFLICT (slot_number) DO NOTHING;

INSERT INTO admins (username, password_hash) VALUES
    ('admin', 'CHANGE_ME_ON_FIRST_RUN')
ON CONFLICT (username) DO NOTHING;
