-- Fix daily_reports table schema to support multiple reports per day
-- This script drops the current table and recreates it with proper constraints

-- Step 1: Drop the existing table (this will remove all data)
DROP TABLE IF EXISTS daily_reports CASCADE;

-- Step 2: Recreate the table with better schema
CREATE TABLE daily_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    executive_summary TEXT NOT NULL,
    run_source VARCHAR(50) DEFAULT 'SCHEDULED',
    generated_at_utc TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Step 3: Add indexes for performance
CREATE INDEX idx_daily_reports_date ON daily_reports(report_date);
CREATE INDEX idx_daily_reports_source ON daily_reports(run_source);
CREATE INDEX idx_daily_reports_created ON daily_reports(created_at);

-- Step 4: Add a composite unique constraint to prevent exact duplicates
-- This allows multiple reports per day but prevents identical reports
CREATE UNIQUE INDEX idx_daily_reports_unique 
ON daily_reports(report_date, run_source, generated_at_utc);

-- Step 5: Add comments for documentation
COMMENT ON TABLE daily_reports IS 'Daily market analysis reports with support for multiple reports per day';
COMMENT ON COLUMN daily_reports.report_date IS 'Date of the report';
COMMENT ON COLUMN daily_reports.run_source IS 'Source of the report (SCHEDULED, ONDEMAND, BACKFILL, TEST)';
COMMENT ON COLUMN daily_reports.generated_at_utc IS 'When the report was generated (UTC)';
COMMENT ON COLUMN daily_reports.created_at IS 'When the record was created in database (UTC)';
