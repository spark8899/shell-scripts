-- init_db.sql

-- Create checkins table
CREATE TABLE IF NOT EXISTS checkins (
    user_id BIGINT,
    username VARCHAR(255),
    checkin_time DATETIME
);

-- Create points table
CREATE TABLE IF NOT EXISTS points (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    points INT
);

-- Create invites table
CREATE TABLE IF NOT EXISTS invites (
    inviter_id BIGINT PRIMARY KEY,
    invite_code VARCHAR(255) UNIQUE,
    uses INT DEFAULT 0
);

-- Create processed_invites table
CREATE TABLE IF NOT EXISTS processed_invites (
    user_id BIGINT,
    invite_code VARCHAR(255),
    processed_time DATETIME
);

-- Create streak table
CREATE TABLE IF NOT EXISTS streak (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    streak_days INT,
    last_checkin DATE
);

-- Create lottery_eligibility table
CREATE TABLE IF NOT EXISTS lottery_eligibility (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    eligible BOOLEAN,
    last_eligible_date DATE,
    weekly_streak INT
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_checkins_user_id ON checkins(user_id);
CREATE INDEX IF NOT EXISTS idx_checkins_checkin_time ON checkins(checkin_time);
CREATE INDEX IF NOT EXISTS idx_processed_invites_user_id ON processed_invites(user_id);
CREATE INDEX IF NOT EXISTS idx_processed_invites_invite_code ON processed_invites(invite_code);
