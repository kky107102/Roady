CREATE TABLE IF NOT EXISTS users (
    id BIGINT NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    name VARCHAR(50) NOT NULL,
    role ENUM('ADMIN', 'INSPECTOR', 'REPAIRER', 'VIEWER') NOT NULL DEFAULT 'VIEWER',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    CONSTRAINT uk_users_username UNIQUE (username),
    CONSTRAINT uk_users_email UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS robots (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'STANDBY',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    CONSTRAINT uk_robots_serial_number UNIQUE (serial_number),
    INDEX idx_robots_user_id (user_id),
    CONSTRAINT fk_robots_user FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS damages (
    id BIGINT NOT NULL AUTO_INCREMENT,
    robot_id BIGINT NULL,
    reported_by BIGINT NOT NULL,
    assigned_to BIGINT NULL,
    description TEXT NULL,
    latitude DECIMAL(10, 7) NULL,
    longitude DECIMAL(10, 7) NULL,
    captured_at DATETIME(6) NULL,
    current_status VARCHAR(30) NOT NULL DEFAULT 'COLLECTED',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_damages_robot_created_at (robot_id, created_at),
    INDEX idx_damages_reported_by_created_at (reported_by, created_at),
    INDEX idx_damages_assigned_to_created_at (assigned_to, created_at),
    CONSTRAINT fk_damages_robot FOREIGN KEY (robot_id) REFERENCES robots (id),
    CONSTRAINT fk_damages_reported_by FOREIGN KEY (reported_by) REFERENCES users (id),
    CONSTRAINT fk_damages_assigned_to FOREIGN KEY (assigned_to) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS damage_images (
    id BIGINT NOT NULL AUTO_INCREMENT,
    damage_id BIGINT NOT NULL,
    sort_order INT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    data LONGBLOB NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_damage_images_damage_sort_order (damage_id, sort_order),
    CONSTRAINT fk_damage_images_damage FOREIGN KEY (damage_id) REFERENCES damages (id) ON DELETE CASCADE
);
