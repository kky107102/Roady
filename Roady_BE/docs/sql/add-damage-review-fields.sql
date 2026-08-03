-- Existing rows are intentionally left with NULL review values.
ALTER TABLE damages
    ADD COLUMN review_damage_type VARCHAR(30) NULL AFTER processing_priority,
    ADD COLUMN review_note VARCHAR(1000) NULL AFTER review_damage_type;
