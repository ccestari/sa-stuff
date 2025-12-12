-- Greenhouse Data Backfill: raw_greenhouse → edna_stream_greenhouse
-- Run this in Redshift Query Editor v2
-- Database: db02

-- Step 1: Create procedure
CREATE OR REPLACE PROCEDURE backfill_greenhouse()
LANGUAGE plpgsql
AS $$
DECLARE
    tbl RECORD;
    missing_count INTEGER;
    inserted_count INTEGER;
BEGIN
    FOR tbl IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'raw_greenhouse'
        ORDER BY tablename
    LOOP
        BEGIN
            EXECUTE format('
                SELECT COUNT(*) 
                FROM raw_greenhouse.%I r
                WHERE NOT EXISTS (
                    SELECT 1 
                    FROM edna_stream_greenhouse.%I s
                    WHERE s.id = r.id
                )', tbl.tablename, tbl.tablename) INTO missing_count;
            
            RAISE INFO 'Table: % - Missing records: %', tbl.tablename, missing_count;
            
            IF missing_count > 0 THEN
                EXECUTE format('
                    INSERT INTO edna_stream_greenhouse.%I
                    SELECT * FROM raw_greenhouse.%I r
                    WHERE NOT EXISTS (
                        SELECT 1 
                        FROM edna_stream_greenhouse.%I s
                        WHERE s.id = r.id
                    )', tbl.tablename, tbl.tablename, tbl.tablename);
                
                GET DIAGNOSTICS inserted_count = ROW_COUNT;
                RAISE INFO 'Table: % - Inserted: % records', tbl.tablename, inserted_count;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE INFO 'Table: % - ERROR: %', tbl.tablename, SQLERRM;
        END;
    END LOOP;
END;
$$;

-- Step 2: Execute procedure
CALL backfill_greenhouse();

-- Step 3: Drop procedure (cleanup)
DROP PROCEDURE backfill_greenhouse();
