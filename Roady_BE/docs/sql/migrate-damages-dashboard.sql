ALTER TABLE damages
    DROP FOREIGN KEY fk_damages_created_by,
    DROP INDEX idx_damages_created_by_created_at,
    CHANGE COLUMN created_by reported_by BIGINT NOT NULL,
    ADD COLUMN robot_id BIGINT NULL AFTER id,
    ADD COLUMN assigned_to BIGINT NULL AFTER reported_by,
    ADD INDEX idx_damages_created_at_id (created_at DESC, id DESC),
    ADD INDEX idx_damages_status_created_at_id (current_status, created_at DESC, id DESC),
    ADD INDEX idx_damages_robot_created_at (robot_id, created_at),
    ADD INDEX idx_damages_reported_by_created_at (reported_by, created_at),
    ADD INDEX idx_damages_assigned_to_created_at (assigned_to, created_at),
    ADD CONSTRAINT fk_damages_robot
        FOREIGN KEY (robot_id) REFERENCES robots (id),
    ADD CONSTRAINT fk_damages_reported_by
        FOREIGN KEY (reported_by) REFERENCES users (id),
    ADD CONSTRAINT fk_damages_assigned_to
        FOREIGN KEY (assigned_to) REFERENCES users (id);
