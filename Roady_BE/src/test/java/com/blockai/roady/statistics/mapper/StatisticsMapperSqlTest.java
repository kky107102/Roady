package com.blockai.roady.statistics.mapper;

import org.apache.ibatis.mapping.BoundSql;
import org.apache.ibatis.session.Configuration;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class StatisticsMapperSqlTest {

    private final Configuration configuration = configuration();

    @Test
    void timeSeriesUsesRequestedUnitAndHalfOpenPeriod() {
        BoundSql boundSql = configuration
                .getMappedStatement(StatisticsMapper.class.getName() + ".findDamageTimeSeries")
                .getBoundSql(Map.of(
                        "from", LocalDateTime.of(2026, 7, 1, 0, 0),
                        "to", LocalDateTime.of(2026, 8, 1, 0, 0),
                        "unit", "MONTH"
                ));

        assertThat(normalize(boundSql.getSql()))
                .contains("DATE_FORMAT(d.created_at, '%Y-%m')")
                .contains("d.created_at >= ?")
                .contains("d.created_at < ?")
                .contains("d.current_status = 'REPAIR_COMPLETED'")
                .contains("GROUP BY period_key")
                .contains("ORDER BY period_key");
    }

    @Test
    void statusStatisticsGroupsByCurrentStatus() {
        BoundSql boundSql = configuration
                .getMappedStatement(StatisticsMapper.class.getName() + ".countDamagesByStatus")
                .getBoundSql(periodParameters());

        assertThat(normalize(boundSql.getSql()))
                .contains("d.current_status AS category")
                .contains("d.created_at >= ?")
                .contains("d.created_at < ?")
                .contains("GROUP BY d.current_status");
    }

    @Test
    void repairPriorityStatisticsUsesLatestSuccessfulAnalysis() {
        BoundSql boundSql = configuration
                .getMappedStatement(StatisticsMapper.class.getName() + ".countDamagesByRepairPriority")
                .getBoundSql(periodParameters());

        assertThat(normalize(boundSql.getSql()))
                .contains("LEFT JOIN damage_ai_analysis_results ai")
                .contains("latest_ai.analysis_status = 'SUCCESS'")
                .contains("ORDER BY latest_ai.created_at DESC, latest_ai.id DESC LIMIT 1")
                .contains("ELSE 'UNCLASSIFIED'")
                .contains("GROUP BY category");
    }

    @Test
    void repairCompletionRateCountsCurrentStatuses() {
        BoundSql boundSql = configuration
                .getMappedStatement(StatisticsMapper.class.getName() + ".countRepairCompletion")
                .getBoundSql(periodParameters());

        assertThat(normalize(boundSql.getSql()))
                .contains("COUNT(*) AS total_count")
                .contains("d.current_status = 'REPAIR_COMPLETED'")
                .contains("d.current_status = 'CANCELED'")
                .contains("d.created_at >= ?")
                .contains("d.created_at < ?");
    }

    private Configuration configuration() {
        Configuration mybatisConfiguration = new Configuration();
        mybatisConfiguration.addMapper(StatisticsMapper.class);
        return mybatisConfiguration;
    }

    private Map<String, LocalDateTime> periodParameters() {
        return Map.of(
                "from", LocalDateTime.of(2026, 7, 1, 0, 0),
                "to", LocalDateTime.of(2026, 8, 1, 0, 0)
        );
    }

    private String normalize(String sql) {
        return sql.replaceAll("\\s+", " ").trim();
    }
}
