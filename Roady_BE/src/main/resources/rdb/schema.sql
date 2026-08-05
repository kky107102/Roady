CREATE TABLE IF NOT EXISTS users (
    id BIGINT NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    name VARCHAR(50) NOT NULL,
    assigned_region_code VARCHAR(10) NULL,
    role ENUM('ADMIN', 'INSPECTOR', 'REPAIRER', 'VIEWER') NOT NULL DEFAULT 'VIEWER',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_users_assigned_region_code (assigned_region_code),
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

CREATE TABLE IF NOT EXISTS robot_status_logs (
    id BIGINT NOT NULL AUTO_INCREMENT,
    robot_id BIGINT NOT NULL,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    battery_level INT NOT NULL,
    operation_status VARCHAR(30) NOT NULL,
    connection_status VARCHAR(30) NOT NULL,
    error_code VARCHAR(100) NULL,
    error_message VARCHAR(500) NULL,
    recorded_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_robot_status_logs_robot_recorded_at (robot_id, recorded_at),
    INDEX idx_robot_status_logs_connection_recorded_at (connection_status, recorded_at),
    CONSTRAINT fk_robot_status_logs_robot FOREIGN KEY (robot_id) REFERENCES robots (id)
);

CREATE TABLE IF NOT EXISTS robot_commands (
    id BIGINT NOT NULL AUTO_INCREMENT,
    robot_id BIGINT NOT NULL,
    requested_by BIGINT NOT NULL,
    command_type ENUM('START_PATROL', 'STOP_PATROL', 'EMERGENCY_STOP', 'RETURN_HOME', 'GET_STATUS') NOT NULL,
    command_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    result_message TEXT NULL,
    requested_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    completed_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    INDEX idx_robot_commands_robot_requested_at (robot_id, requested_at),
    INDEX idx_robot_commands_status_requested_at (command_status, requested_at),
    CONSTRAINT fk_robot_commands_robot FOREIGN KEY (robot_id) REFERENCES robots (id),
    CONSTRAINT fk_robot_commands_requested_by FOREIGN KEY (requested_by) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS robot_routes (
    id BIGINT NOT NULL AUTO_INCREMENT,
    robot_id BIGINT NOT NULL,
    created_by BIGINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    route_status VARCHAR(30) NOT NULL DEFAULT 'CREATED',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_robot_routes_robot_status (robot_id, route_status),
    INDEX idx_robot_routes_created_by_created_at (created_by, created_at),
    CONSTRAINT fk_robot_routes_robot FOREIGN KEY (robot_id) REFERENCES robots (id),
    CONSTRAINT fk_robot_routes_created_by FOREIGN KEY (created_by) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS robot_route_points (
    id BIGINT NOT NULL AUTO_INCREMENT,
    route_id BIGINT NOT NULL,
    point_order INT NOT NULL,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    point_type VARCHAR(30) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_robot_route_points_route_order (route_id, point_order),
    CONSTRAINT fk_robot_route_points_route FOREIGN KEY (route_id) REFERENCES robot_routes (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS damages (
    id BIGINT NOT NULL AUTO_INCREMENT,
    robot_id BIGINT NULL,
    reported_by BIGINT NOT NULL,
    assigned_to BIGINT NULL,
    description TEXT NULL,
    address_name VARCHAR(255) NULL,
    road_address_name VARCHAR(255) NULL,
    region_code VARCHAR(10) NULL,
    region_1depth_name VARCHAR(100) NULL,
    region_2depth_name VARCHAR(100) NULL,
    region_3depth_name VARCHAR(100) NULL,
    geocoded_at DATETIME(6) NULL,
    latitude DECIMAL(10, 7) NULL,
    longitude DECIMAL(10, 7) NULL,
    captured_at DATETIME(6) NULL,
    current_status VARCHAR(30) NOT NULL DEFAULT 'COLLECTED',
    processing_priority VARCHAR(30) NULL,
    review_damage_type VARCHAR(30) NULL,
    review_note VARCHAR(1000) NULL,
    repairer_id BIGINT NULL,
    repair_completed_at DATE NULL,
    repair_completion_note VARCHAR(1000) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_damages_created_at_id (created_at DESC, id DESC),
    INDEX idx_damages_status_created_at_id (current_status, created_at DESC, id DESC),
    INDEX idx_damages_statistics_created_status (created_at, current_status),
    INDEX idx_damages_robot_created_at (robot_id, created_at),
    INDEX idx_damages_reported_by_created_at (reported_by, created_at),
    INDEX idx_damages_assigned_to_created_at (assigned_to, created_at),
    INDEX idx_damages_repairer_created_at (repairer_id, created_at),
    INDEX idx_damages_address_name (address_name),
    INDEX idx_damages_road_address_name (road_address_name),
    INDEX idx_damages_region_code_created_at (region_code, created_at DESC, id DESC),
    INDEX idx_damages_latitude_longitude (latitude, longitude),
    CONSTRAINT fk_damages_robot FOREIGN KEY (robot_id) REFERENCES robots (id),
    CONSTRAINT fk_damages_reported_by FOREIGN KEY (reported_by) REFERENCES users (id),
    CONSTRAINT fk_damages_assigned_to FOREIGN KEY (assigned_to) REFERENCES users (id),
    CONSTRAINT fk_damages_repairer FOREIGN KEY (repairer_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS repair_request_histories (
    id BIGINT NOT NULL AUTO_INCREMENT,
    damage_id BIGINT NOT NULL,
    repair_assignment_id BIGINT NULL,
    requested_by BIGINT NOT NULL,
    repairer_id BIGINT NULL,
    before_status VARCHAR(30) NOT NULL,
    after_status VARCHAR(30) NOT NULL,
    note VARCHAR(1000) NULL,
    requested_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_repair_request_histories_damage_requested_at (damage_id, requested_at DESC),
    INDEX idx_repair_request_histories_assignment_requested_at (repair_assignment_id, requested_at DESC),
    CONSTRAINT fk_repair_request_histories_damage FOREIGN KEY (damage_id) REFERENCES damages (id) ON DELETE CASCADE,
    CONSTRAINT fk_repair_request_histories_requested_by FOREIGN KEY (requested_by) REFERENCES users (id),
    CONSTRAINT fk_repair_request_histories_repairer FOREIGN KEY (repairer_id) REFERENCES users (id)
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

CREATE TABLE IF NOT EXISTS damage_ai_analysis_results (
    id BIGINT NOT NULL AUTO_INCREMENT,
    damage_id BIGINT NOT NULL,
    damaged BOOLEAN NULL,
    damage_score INT NULL,
    damage_type VARCHAR(30) NULL,
    repair_required BOOLEAN NULL,
    repair_priority VARCHAR(30) NULL,
    confidence_score DECIMAL(5, 4) NULL,
    analysis_status VARCHAR(30) NOT NULL DEFAULT 'QUEUED',
    raw_result LONGTEXT NULL,
    analyzed_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_damage_ai_analysis_results_damage_created_at (damage_id, created_at),
    INDEX idx_damage_ai_analysis_results_status_created_at (analysis_status, created_at),
    INDEX idx_damage_ai_damage_status_created_id (
        damage_id,
        analysis_status,
        created_at DESC,
        id DESC
    ),
    CONSTRAINT fk_damage_ai_analysis_results_damage FOREIGN KEY (damage_id) REFERENCES damages (id) ON DELETE CASCADE
);
