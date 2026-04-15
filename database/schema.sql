-- ============================================================
-- AIEMCS - AI Powered Equipment Monitoring and Control System
-- Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS aiemcs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE aiemcs;

-- ============================================================
-- TABLE: source_data
-- Vendors / suppliers who provide equipment
-- ============================================================
CREATE TABLE IF NOT EXISTS source_data (
    source_id       INT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(150),
    phone           VARCHAR(20),
    room_duty       VARCHAR(20),     -- e.g. E_402
    faculty         VARCHAR(100),
    department      VARCHAR(100),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE: incharge_data
-- Lab incharges responsible for equipment rooms
-- ============================================================
CREATE TABLE IF NOT EXISTS incharge_data (
    incharge_id     INT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(150) UNIQUE,
    phone           VARCHAR(20),
    room_duty       VARCHAR(20),     -- e.g. E_109
    password_hash   VARCHAR(255),    -- bcrypt hash
    role            VARCHAR(20) DEFAULT 'incharge',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE: equipment_data
-- Core equipment inventory
-- ============================================================
CREATE TABLE IF NOT EXISTS equipment_data (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    tag                     VARCHAR(100) UNIQUE NOT NULL,
    equipment_name          VARCHAR(150) NOT NULL,
    equipment_category      VARCHAR(100) NOT NULL,
    equipment_model_details TEXT,
    unit_price              DECIMAL(12,2),
    date_of_purchase        DATE,
    quantity                INT DEFAULT 1,
    working_status          VARCHAR(50) DEFAULT 'good',   -- good / faulty / maintenance
    faculty                 VARCHAR(100),
    deparment               VARCHAR(100),
    block_location          VARCHAR(20),   -- e.g. E_316
    source_id               INT,
    incharge_id             INT,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id)   REFERENCES source_data(source_id)   ON DELETE SET NULL,
    FOREIGN KEY (incharge_id) REFERENCES incharge_data(incharge_id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE: equipment_utilization
-- Timetable / schedule of equipment usage
-- ============================================================
CREATE TABLE IF NOT EXISTS equipment_utilization (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    block_location  VARCHAR(20) NOT NULL,  -- e.g. E_100
    type            VARCHAR(50),           -- lab / classroom / hall
    day             VARCHAR(20),           -- Monday ... Sunday
    slot            VARCHAR(100),          -- 09:00-10:00, 10:00-11:00
    activity        VARCHAR(200),          -- free / subject name / event
    incharge_id     INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incharge_id) REFERENCES incharge_data(incharge_id) ON DELETE SET NULL
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_equip_location  ON equipment_data(block_location);
CREATE INDEX idx_equip_category  ON equipment_data(equipment_category);
CREATE INDEX idx_equip_status    ON equipment_data(working_status);
CREATE INDEX idx_util_location   ON equipment_utilization(block_location);
CREATE INDEX idx_util_day        ON equipment_utilization(day);
