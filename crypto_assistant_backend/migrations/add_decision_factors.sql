-- Migration: Add decision_factors and total_score columns to signals table
-- Date: 2025-06-11
-- Description: Add support for storing detailed signal decision factors and total score

-- Add decision_factors column as JSON
ALTER TABLE crypto.signals 
ADD COLUMN IF NOT EXISTS decision_factors JSON;

-- Add total_score column as INTEGER
ALTER TABLE crypto.signals 
ADD COLUMN IF NOT EXISTS total_score INTEGER DEFAULT 0;

-- Add comment for documentation
COMMENT ON COLUMN crypto.signals.decision_factors IS 'JSON object containing detailed decision factors for signal generation';
COMMENT ON COLUMN crypto.signals.total_score IS 'Total score calculated from all decision factors';

-- Create index on total_score for performance
CREATE INDEX IF NOT EXISTS idx_signals_total_score ON crypto.signals(total_score);

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_schema = 'crypto' 
  AND table_name = 'signals' 
  AND column_name IN ('decision_factors', 'total_score');