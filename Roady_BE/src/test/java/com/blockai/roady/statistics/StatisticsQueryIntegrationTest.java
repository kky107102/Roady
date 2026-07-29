package com.blockai.roady.statistics;

import com.blockai.roady.statistics.domain.StatisticsPeriod;
import com.blockai.roady.statistics.domain.StatisticsUnit;
import com.blockai.roady.statistics.service.StatisticsService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@Transactional
class StatisticsQueryIntegrationTest {

    private static final LocalDateTime FROM = LocalDateTime.of(2098, 7, 1, 0, 0);
    private static final LocalDateTime TO = LocalDateTime.of(2098, 7, 4, 0, 0);

    @Autowired
    private StatisticsService statisticsService;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    private Long collectedDamageId;
    private Long completedDamageId;

    @BeforeEach
    void setUpStatisticsData() {
        Long reportedBy = userId("admin");
        collectedDamageId = insertDamage(
                reportedBy,
                "COLLECTED",
                LocalDateTime.of(2098, 7, 1, 10, 0)
        );
        completedDamageId = insertDamage(
                reportedBy,
                "REPAIR_COMPLETED",
                LocalDateTime.of(2098, 7, 1, 11, 0)
        );
        insertDamage(
                reportedBy,
                "REPAIR_NOT_REQUIRED",
                LocalDateTime.of(2098, 7, 3, 9, 0)
        );
        insertDamage(
                reportedBy,
                "REPAIR_COMPLETED",
                TO
        );

        insertAnalysis(
                collectedDamageId,
                "NORMAL",
                "SUCCESS",
                LocalDateTime.of(2098, 7, 1, 10, 10)
        );
        insertAnalysis(
                collectedDamageId,
                "URGENT",
                "SUCCESS",
                LocalDateTime.of(2098, 7, 1, 10, 20)
        );
        insertAnalysis(
                collectedDamageId,
                null,
                "FAILED",
                LocalDateTime.of(2098, 7, 1, 10, 30)
        );
        insertAnalysis(
                completedDamageId,
                "HIGH",
                "SUCCESS",
                LocalDateTime.of(2098, 7, 1, 11, 10)
        );
    }

    @Test
    void timeSeriesUsesHalfOpenPeriodAndFillsMissingDays() {
        var result = statisticsService.getDamageTimeSeries(
                new StatisticsPeriod(FROM, TO),
                StatisticsUnit.DAY
        );

        assertThat(result.items()).hasSize(3);
        assertThat(result.items().get(0).period()).isEqualTo("2098-07-01");
        assertThat(result.items().get(0).totalCount()).isEqualTo(2);
        assertThat(result.items().get(0).repairCompletedCount()).isEqualTo(1);
        assertThat(result.items().get(0).repairCompletionRate()).isEqualByComparingTo("50.00");
        assertThat(result.items().get(1).period()).isEqualTo("2098-07-02");
        assertThat(result.items().get(1).totalCount()).isZero();
        assertThat(result.items().get(2).totalCount()).isEqualTo(1);
    }

    @Test
    void categoricalAndCompletionStatisticsUseTheSamePeriod() {
        var period = new StatisticsPeriod(FROM, TO);

        var statuses = statisticsService.getDamageStatusStatistics(period);
        var priorities = statisticsService.getRepairPriorityStatistics(period);
        var completion = statisticsService.getRepairCompletionRate(period);

        assertThat(statuses.totalCount()).isEqualTo(3);
        assertThat(statuses.counts())
                .containsEntry("COLLECTED", 1L)
                .containsEntry("REPAIR_COMPLETED", 1L)
                .containsEntry("REPAIR_NOT_REQUIRED", 1L);

        assertThat(priorities.totalCount()).isEqualTo(3);
        assertThat(priorities.classifiedCount()).isEqualTo(2);
        assertThat(priorities.unclassifiedCount()).isEqualTo(1);
        assertThat(priorities.counts())
                .containsEntry("URGENT", 1L)
                .containsEntry("HIGH", 1L)
                .containsEntry("NORMAL", 0L);

        assertThat(completion.totalCount()).isEqualTo(3);
        assertThat(completion.completedCount()).isEqualTo(1);
        assertThat(completion.notRequiredCount()).isEqualTo(1);
        assertThat(completion.completionRate()).isEqualByComparingTo("33.33");
    }

    private Long userId(String username) {
        return jdbcTemplate.queryForObject(
                "SELECT id FROM users WHERE username = ?",
                Long.class,
                username
        );
    }

    private Long insertDamage(Long reportedBy, String status, LocalDateTime createdAt) {
        String description = "statistics-query-" + UUID.randomUUID();
        jdbcTemplate.update(
                """
                INSERT INTO damages (
                    reported_by,
                    description,
                    current_status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                reportedBy,
                description,
                status,
                createdAt,
                createdAt
        );
        return jdbcTemplate.queryForObject(
                "SELECT id FROM damages WHERE description = ?",
                Long.class,
                description
        );
    }

    private void insertAnalysis(
            Long damageId,
            String repairPriority,
            String analysisStatus,
            LocalDateTime createdAt
    ) {
        jdbcTemplate.update(
                """
                INSERT INTO damage_ai_analysis_results (
                    damage_id,
                    repair_priority,
                    analysis_status,
                    analyzed_at,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                damageId,
                repairPriority,
                analysisStatus,
                createdAt,
                createdAt
        );
    }
}
