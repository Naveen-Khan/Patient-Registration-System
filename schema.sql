-- Supabase Database Schema for Patient Registration

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create patients table
CREATE TABLE IF NOT EXISTS patients (
    patient_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    first_name TEXT NOT NULL CHECK (first_name ~ '^[A-Za-z\'\-]{1,50}$'),
    last_name TEXT NOT NULL CHECK (last_name ~ '^[A-Za-z\'\-]{1,50}$'),
    date_of_birth DATE NOT NULL CHECK (date_of_birth <= CURRENT_DATE),
    sex TEXT NOT NULL CHECK (sex IN ('Male', 'Female', 'Other', 'Decline to Answer')),
    phone_number TEXT NOT NULL,
    address_line_1 TEXT NOT NULL,
    city TEXT NOT NULL CHECK (length(city) <= 100),
    state TEXT NOT NULL CHECK (state ~ '^[A-Z]{2}$'),
    zip_code TEXT NOT NULL CHECK (zip_code ~ '^\d{5}(-\d{4})?$'),
    email TEXT CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    address_line_2 TEXT,
    insurance_provider TEXT,
    insurance_member_id TEXT,
    preferred_language TEXT DEFAULT 'English',
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Index for phone lookups (for duplicate detection)
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients (phone_number) WHERE deleted_at IS NULL;

-- Index for name lookups
CREATE INDEX IF NOT EXISTS idx_patients_last_name ON patients (last_name) WHERE deleted_at IS NULL;

-- Index for date of birth lookups
CREATE INDEX IF NOT EXISTS idx_patients_dob ON patients (date_of_birth) WHERE deleted_at IS NULL;

-- Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security: Enable RLS
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

-- Policy: Everyone can read (for the API)
CREATE POLICY "Public read access" ON patients
    FOR SELECT USING (deleted_at IS NULL);

-- Policy: Service role can do everything (via service_role key)
-- The service_role key bypasses RLS entirely

-- Insert seed data
INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, sex, phone_number, address_line_1, city, state, zip_code, preferred_language, created_at, updated_at)
VALUES
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Jane', 'Doe', '1985-03-15', 'Female', '5551234567', '123 Main St', 'Springfield', 'IL', '62701', 'English', NOW(), NOW()),
    ('b2c3d4e5-f6a7-8901-bcde-f12345678901', 'John', 'Smith', '1990-07-22', 'Male', '5559876543', '456 Oak Ave', 'Chicago', 'IL', '60601', 'English', NOW(), NOW());
