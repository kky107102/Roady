CREATE INDEX idx_damages_statistics_created_status
    ON damages (created_at, current_status);

CREATE INDEX idx_damage_ai_damage_status_created_id
    ON damage_ai_analysis_results (
        damage_id,
        analysis_status,
        created_at DESC,
        id DESC
    );
