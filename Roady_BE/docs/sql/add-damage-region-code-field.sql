ALTER TABLE damages
    ADD COLUMN region_code VARCHAR(10) NULL AFTER road_address_name;

CREATE INDEX idx_damages_region_code_created_at
    ON damages (region_code, created_at DESC, id DESC);
