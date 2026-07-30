ALTER TABLE users
    ADD COLUMN assigned_region_code VARCHAR(10) NULL AFTER name;

CREATE INDEX idx_users_assigned_region_code
    ON users (assigned_region_code);
