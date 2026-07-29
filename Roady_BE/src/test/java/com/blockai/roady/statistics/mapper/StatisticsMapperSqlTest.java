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

    private Configuration configuration() {
        Configuration mybatisConfiguration = new Configuration();
        mybatisConfiguration.addMapper(StatisticsMapper.class);
        return mybatisConfiguration;
    }

    private String normalize(String sql) {
        return sql.replaceAll("\\s+", " ").trim();
    }
}
