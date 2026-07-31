package com.blockai.roady.damage.mapper;

import org.apache.ibatis.mapping.BoundSql;
import org.apache.ibatis.session.Configuration;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class DamageMapperSqlTest {

    private final Configuration configuration = configuration();

    @Test
    void findSummaryByIdSelectsReportedBy() {
        BoundSql boundSql = configuration
                .getMappedStatement(DamageMapper.class.getName() + ".findSummaryById")
                .getBoundSql(Map.of("id", 1L));

        assertThat(normalize(boundSql.getSql()))
                .contains("d.reported_by")
                .contains("WHERE d.id = ?");
    }

    @Test
    void searchSummariesBuildsFilteredPageQuery() {
        Map<String, Object> parameters = searchParameters();

        BoundSql boundSql = configuration
                .getMappedStatement(DamageMapper.class.getName() + ".searchSummaries")
                .getBoundSql(parameters);

        assertThat(normalize(boundSql.getSql()))
                .contains("LEFT JOIN damage_ai_analysis_results ai")
                .contains("latest_ai.analysis_status = 'SUCCESS'")
                .contains("ORDER BY latest_ai.created_at DESC, latest_ai.id DESC LIMIT 1")
                .contains("WHERE d.created_at >= ?")
                .contains("AND d.created_at < ?")
                .contains("AND d.current_status = ?")
                .contains("AND d.robot_id = ?")
                .contains("AND d.assigned_to = ?")
                .contains("AND d.region_code = ?")
                .contains("ORDER BY d.created_at DESC, d.id DESC")
                .contains("LIMIT ?, ?");
    }

    @Test
    void countSummariesUsesSameFiltersWithoutPagination() {
        Map<String, Object> parameters = searchParameters();

        BoundSql boundSql = configuration
                .getMappedStatement(DamageMapper.class.getName() + ".countSummaries")
                .getBoundSql(parameters);

        assertThat(normalize(boundSql.getSql()))
                .contains("SELECT COUNT(*)")
                .contains("WHERE d.created_at >= ?")
                .contains("AND d.created_at < ?")
                .contains("AND d.current_status = ?")
                .contains("AND d.robot_id = ?")
                .contains("AND d.assigned_to = ?")
                .contains("AND d.region_code = ?")
                .doesNotContain("LIMIT")
                .doesNotContain("ORDER BY");
    }

    @Test
    void summarizeByStatusBuildsGroupedFilterQuery() {
        Map<String, Object> parameters = searchParameters();

        BoundSql boundSql = configuration
                .getMappedStatement(DamageMapper.class.getName() + ".summarizeByStatus")
                .getBoundSql(parameters);

        assertThat(normalize(boundSql.getSql()))
                .contains("COUNT(*) AS total")
                .contains("SUM(CASE WHEN d.assigned_to IS NULL THEN 1 ELSE 0 END) AS unassigned")
                .contains("WHERE d.created_at >= ?")
                .contains("AND d.created_at < ?")
                .contains("AND d.current_status = ?")
                .contains("AND d.robot_id = ?")
                .contains("AND d.assigned_to = ?")
                .contains("AND d.region_code = ?")
                .contains("GROUP BY d.current_status")
                .doesNotContain("LIMIT");
    }

    @Test
    void findMapMarkersBuildsCoordinateFilterQuery() {
        Map<String, Object> parameters = searchParameters();

        BoundSql boundSql = configuration
                .getMappedStatement(DamageMapper.class.getName() + ".findMapMarkers")
                .getBoundSql(parameters);

        assertThat(normalize(boundSql.getSql()))
                .contains("d.latitude BETWEEN ? AND ?")
                .contains("d.longitude BETWEEN ? AND ?")
                .contains("AND d.created_at >= ?")
                .contains("AND d.created_at < ?")
                .contains("AND d.current_status = ?")
                .contains("AND d.robot_id = ?")
                .contains("AND d.assigned_to = ?")
                .contains("AND d.region_code = ?")
                .contains("ORDER BY d.created_at DESC, d.id DESC")
                .doesNotContain("JOIN")
                .doesNotContain("LIMIT");
    }

    private Configuration configuration() {
        Configuration mybatisConfiguration = new Configuration();
        mybatisConfiguration.addMapper(DamageMapper.class);
        return mybatisConfiguration;
    }

    private Map<String, Object> searchParameters() {
        Map<String, Object> parameters = new HashMap<>();
        parameters.put("from", LocalDateTime.of(2026, 7, 1, 0, 0));
        parameters.put("to", LocalDateTime.of(2026, 8, 1, 0, 0));
        parameters.put("status", "AI_ANALYZED");
        parameters.put("robotId", 1L);
        parameters.put("assignedTo", 5L);
        parameters.put("regionCode", "41550");
        parameters.put("south", new BigDecimal("37.45"));
        parameters.put("north", new BigDecimal("37.62"));
        parameters.put("west", new BigDecimal("126.80"));
        parameters.put("east", new BigDecimal("127.10"));
        parameters.put("offset", 20L);
        parameters.put("size", 20);
        return parameters;
    }

    private String normalize(String sql) {
        return sql.replaceAll("\\s+", " ").trim();
    }
}
