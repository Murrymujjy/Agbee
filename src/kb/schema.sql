-- Àgbẹ̀ structured knowledge base — 6 tables, every row carries source_id for citation.
-- See proposal Section 5.3.

CREATE TABLE IF NOT EXISTS crop_calendar (
    id INTEGER PRIMARY KEY,
    crop TEXT NOT NULL,
    zone TEXT,
    state TEXT,
    operation TEXT NOT NULL,      -- e.g. 'planting', 'first_fertilizer', 'harvest'
    start_month INTEGER,
    end_month INTEGER,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS spacing (
    id INTEGER PRIMARY KEY,
    crop TEXT NOT NULL,
    variety_class TEXT,
    row_cm REAL,
    within_row_cm REAL,
    plants_per_ha REAL,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fertilizer_rate (
    id INTEGER PRIMARY KEY,
    crop TEXT NOT NULL,
    nutrient TEXT NOT NULL,        -- e.g. 'NPK 15-15-15', 'Urea'
    kg_per_ha REAL,
    timing TEXT,
    split_number INTEGER,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agrochemical (
    id INTEGER PRIMARY KEY,
    product TEXT NOT NULL,
    active_ingredient TEXT,
    target TEXT,                    -- pest/disease/weed targeted
    crop TEXT,
    rate_per_ha REAL,
    pre_harvest_interval_days INTEGER,
    source_id TEXT NOT NULL          -- must cross-check against NAFDAC registration
);

CREATE TABLE IF NOT EXISTS variety (
    id INTEGER PRIMARY KEY,
    crop TEXT NOT NULL,
    name TEXT NOT NULL,
    maturity_days INTEGER,
    zone TEXT,
    traits TEXT,
    source_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pest (
    id INTEGER PRIMARY KEY,
    crop TEXT NOT NULL,
    name TEXT NOT NULL,
    symptoms TEXT,
    affected_stage TEXT,
    cultural_control TEXT,
    chemical_control TEXT,
    source_id TEXT NOT NULL
);

-- Provenance: every source_id used above must resolve to a row here.
CREATE TABLE IF NOT EXISTS source (
    source_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    publisher TEXT,
    year INTEGER,
    url_or_reference TEXT,
    license_note TEXT NOT NULL      -- redistribution terms — never leave blank
);
