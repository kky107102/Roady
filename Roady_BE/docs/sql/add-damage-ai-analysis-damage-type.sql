ALTER TABLE damage_ai_analysis_results
    ADD COLUMN damage_type VARCHAR(30) NULL AFTER damage_score;
