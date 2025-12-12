-- Redshift table setup for period attendance data
-- Cluster: edna-prod-dw
-- Database: db02
-- Schema: ioesd (existing schema - will not create dependencies)
-- Note: This creates a NEW table (api_period_attendance) to avoid conflicts with existing periodattendance table

-- 1. Create external schema for S3 data (Spectrum)
CREATE EXTERNAL SCHEMA IF NOT EXISTS esd_spectrum
FROM DATA CATALOG
DATABASE 'esd_period_attendance'
IAM_ROLE 'arn:aws:iam::309820967897:role/RedshiftSpectrumRole'
CREATE EXTERNAL DATABASE IF NOT EXISTS;

-- 2. Create external table for partitioned S3 data
CREATE EXTERNAL TABLE esd_spectrum.api_period_attendance (
    id BIGINT,
    date VARCHAR(20),
    studentId BIGINT,
    meetingTimeId BIGINT,
    meetingTime_id BIGINT,
    meetingTime_sectionId BIGINT,
    meetingTime_roomNumber VARCHAR(50),
    meetingTime_semesterNumbers VARCHAR(100),
    meetingTime_bellScheduleDay VARCHAR(50),
    meetingTime_periodFrom VARCHAR(20),
    meetingTime_periodTo VARCHAR(20),
    meetingTime_startTime VARCHAR(20),
    meetingTime_endTime VARCHAR(20),
    meetingTime_roomId BIGINT,
    meetingTime_cycle VARCHAR(50),
    meetingTime_teacher VARCHAR(200),
    meetingTime_teachers VARCHAR(500),
    meetingTime_markingPeriods VARCHAR(200),
    meetingTime_semesterPattern VARCHAR(100),
    meetingTime_friendlyName VARCHAR(200),
    attendanceReasonId BIGINT,
    attendanceReason VARCHAR(200),
    modality VARCHAR(50),
    attendanceStatus VARCHAR(50),
    excusedStatus VARCHAR(50),
    isEarlyDismissal BOOLEAN,
    earlyDismissalAttendanceReasonId BIGINT,
    minutesLate INTEGER,
    minutesEarly INTEGER,
    minutesMissed INTEGER,
    actualMinutes INTEGER,
    potentialMinutes INTEGER,
    tardyTime VARCHAR(50),
    dismissedTime VARCHAR(50),
    comment VARCHAR(1000),
    isLocked BOOLEAN,
    verified BOOLEAN,
    createdBy BIGINT,
    createdOn VARCHAR(50),
    modifiedBy BIGINT,
    modifiedOn VARCHAR(50)
)
PARTITIONED BY (year INTEGER, month INTEGER, day INTEGER)
STORED AS PARQUET
LOCATION 's3://edna-prod/raw_esd/incoming/periodAttendance/operational/landing/unnested_period_attendance/';

-- 3. Add partitions (run after data upload)
-- ALTER TABLE esd_spectrum.period_attendance ADD PARTITION (year=2025, month=12, day=09) 
-- LOCATION 's3://edna-prod/raw_esd/incoming/periodAttendance/operational/landing/unnested_period_attendance/year=2025/month=12/day=09/';

-- 4. Create Redshift native table in ioesd schema (no dependencies on existing tables)
CREATE TABLE IF NOT EXISTS ioesd.api_period_attendance (
    id BIGINT,
    attendance_date DATE,
    student_id BIGINT,
    meeting_time_id BIGINT,
    section_id BIGINT,
    room_number VARCHAR(50),
    period_from VARCHAR(20),
    period_to VARCHAR(20),
    start_time VARCHAR(20),
    end_time VARCHAR(20),
    attendance_reason VARCHAR(200),
    modality VARCHAR(50),
    attendance_status VARCHAR(50),
    excused_status VARCHAR(50),
    is_early_dismissal BOOLEAN,
    minutes_late INTEGER,
    minutes_early INTEGER,
    minutes_missed INTEGER,
    actual_minutes INTEGER,
    potential_minutes INTEGER,
    created_on TIMESTAMP,
    modified_on TIMESTAMP,
    year INTEGER,
    month INTEGER,
    day INTEGER
)
DISTKEY(student_id)
SORTKEY(attendance_date, student_id);

-- 5. Load data from external table to Redshift table
-- INSERT INTO ioesd.api_period_attendance
-- SELECT 
--     id,
--     TO_DATE(date, 'MM-DD-YYYY') as attendance_date,
--     studentId as student_id,
--     meetingTimeId as meeting_time_id,
--     meetingTime_sectionId as section_id,
--     meetingTime_roomNumber as room_number,
--     meetingTime_periodFrom as period_from,
--     meetingTime_periodTo as period_to,
--     meetingTime_startTime as start_time,
--     meetingTime_endTime as end_time,
--     attendanceReason as attendance_reason,
--     modality,
--     attendanceStatus as attendance_status,
--     excusedStatus as excused_status,
--     isEarlyDismissal as is_early_dismissal,
--     minutesLate as minutes_late,
--     minutesEarly as minutes_early,
--     minutesMissed as minutes_missed,
--     actualMinutes as actual_minutes,
--     potentialMinutes as potential_minutes,
--     CAST(createdOn AS TIMESTAMP) as created_on,
--     CAST(modifiedOn AS TIMESTAMP) as modified_on,
--     year,
--     month,
--     day
-- FROM esd_spectrum.api_period_attendance
-- WHERE year = 2025 AND month = 12 AND day = 9;

-- 6. Grant permissions (optional)
-- GRANT SELECT ON ioesd.api_period_attendance TO GROUP analysts;

-- Note: This table is completely independent and does not affect:
--   - ioesd.periodattendance (existing table)
--   - ioesd.raw_periodattendance (existing table)
--   - Any other existing tables in ioesd schema
