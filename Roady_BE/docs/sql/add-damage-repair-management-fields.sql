ALTER TABLE damages
    ADD COLUMN repairer_id BIGINT NULL AFTER review_note,
    ADD COLUMN repair_completed_at DATE NULL AFTER repairer_id,
    ADD COLUMN repair_completion_note VARCHAR(1000) NULL AFTER repair_completed_at,
    ADD INDEX idx_damages_repairer_created_at (repairer_id, created_at),
    ADD CONSTRAINT fk_damages_repairer FOREIGN KEY (repairer_id) REFERENCES users (id);
