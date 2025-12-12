-- Find all schemas in db02
SELECT nspname 
FROM pg_namespace 
WHERE nspname NOT LIKE 'pg_%' 
  AND nspname != 'information_schema'
ORDER BY nspname;
