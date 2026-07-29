CREATE INDEX idx_damages_created_at_id
    ON damages (created_at DESC, id DESC);

CREATE INDEX idx_damages_status_created_at_id
    ON damages (current_status, created_at DESC, id DESC);

CREATE INDEX idx_damages_latitude_longitude
    ON damages (latitude, longitude);
