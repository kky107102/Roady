ALTER TABLE damages
    ADD COLUMN address_name VARCHAR(255) NULL AFTER description,
    ADD COLUMN road_address_name VARCHAR(255) NULL AFTER address_name,
    ADD COLUMN region_1depth_name VARCHAR(100) NULL AFTER road_address_name,
    ADD COLUMN region_2depth_name VARCHAR(100) NULL AFTER region_1depth_name,
    ADD COLUMN region_3depth_name VARCHAR(100) NULL AFTER region_2depth_name,
    ADD COLUMN geocoded_at DATETIME(6) NULL AFTER region_3depth_name;

CREATE INDEX idx_damages_address_name
    ON damages (address_name);

CREATE INDEX idx_damages_road_address_name
    ON damages (road_address_name);
