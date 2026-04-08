-- ============================================================
-- SunLeo Database Schema
-- Assignment 8: Data Access Layer
-- Database Engine: SQLite 3
-- ============================================================

-- -----------------------------------------------------------
-- Table: jobs
-- Purpose: Persist YouTube-to-MP3 conversion job records.
--          Previously stored in an in-memory Python dict,
--          which meant all job data was lost on server restart.
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS jobs (
    job_id      TEXT    PRIMARY KEY,                         -- UUID hex string
    url         TEXT    NOT NULL,                            -- Original YouTube URL
    video_id    TEXT    NOT NULL,                            -- Extracted YouTube video ID
    status      TEXT    NOT NULL DEFAULT 'queued',           -- queued | running | completed | failed
    title       TEXT,                                       -- Video title (populated after download)
    file_path   TEXT,                                       -- Absolute path to downloaded MP3
    error       TEXT,                                       -- Error message if job failed
    metadata    TEXT,                                       -- JSON blob of video metadata
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),  -- ISO 8601 UTC timestamp
    started_at  TEXT,                                       -- When processing began
    finished_at TEXT                                        -- When processing ended
);

-- Index for cleanup queries that filter by finished_at
CREATE INDEX IF NOT EXISTS idx_jobs_finished_at ON jobs(finished_at);

-- Index for status-based lookups
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);


-- -----------------------------------------------------------
-- Table: feedback
-- Purpose: Store user feedback submissions.
--          Previously saved to a flat JSON file on disk,
--          which made querying and filtering impossible.
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,          -- Auto-incrementing ID
    name        TEXT    NOT NULL,                            -- Submitter's name
    email       TEXT    NOT NULL,                            -- Submitter's email
    category    TEXT    NOT NULL,                            -- Bug Report | Feature Request | General Feedback | Other
    message     TEXT    NOT NULL,                            -- Feedback content
    timestamp   TEXT    NOT NULL DEFAULT (datetime('now'))   -- ISO 8601 UTC timestamp
);

-- Index for category-based filtering
CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback(category);
