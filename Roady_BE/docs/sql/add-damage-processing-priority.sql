ALTER TABLE damages
    ADD COLUMN processing_priority VARCHAR(30) NULL AFTER current_status;
