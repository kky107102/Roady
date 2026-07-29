package com.blockai.roady.statistics.service;

import com.blockai.roady.statistics.domain.DamageTimeSeriesRow;
import com.blockai.roady.statistics.domain.StatisticsCountRow;
import com.blockai.roady.statistics.domain.RepairCompletionCounts;
import com.blockai.roady.statistics.domain.StatisticsPeriod;
import com.blockai.roady.statistics.domain.StatisticsUnit;
import com.blockai.roady.statistics.mapper.StatisticsMapper;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class StatisticsServiceTest {

    private final StatisticsMapper statisticsMapper = mock(StatisticsMapper.class);
    private final StatisticsService statisticsService = new StatisticsService(statisticsMapper);

    @Test
    void fillsMissingPeriodsAndCalculatesCompletionRate() {
        var period = new StatisticsPeriod(
                LocalDateTime.of(2026, 7, 1, 0, 0),
                LocalDateTime.of(2026, 7, 4, 0, 0)
        );
        when(statisticsMapper.findDamageTimeSeries(period.from(), period.to(), "DAY"))
                .thenReturn(List.of(
                        new DamageTimeSeriesRow("2026-07-01", 3, 1),
                        new DamageTimeSeriesRow("2026-07-03", 2, 1)
                ));

        var result = statisticsService.getDamageTimeSeries(period, StatisticsUnit.DAY);

        assertThat(result.items()).hasSize(3);
        assertThat(result.items().get(0).repairCompletionRate()).isEqualByComparingTo("33.33");
        assertThat(result.items().get(1).period()).isEqualTo("2026-07-02");
        assertThat(result.items().get(1).totalCount()).isZero();
        assertThat(result.items().get(1).repairCompletionRate()).isEqualByComparingTo("0.00");
        assertThat(result.items().get(2).repairCompletionRate()).isEqualByComparingTo("50.00");
    }

    @Test
    void fillsMissingDamageStatusesWithZero() {
        var period = period();
        when(statisticsMapper.countDamagesByStatus(period.from(), period.to()))
                .thenReturn(List.of(
                        new StatisticsCountRow("COLLECTED", 3),
                        new StatisticsCountRow("REPAIR_COMPLETED", 2)
                ));

        var result = statisticsService.getDamageStatusStatistics(period);

        assertThat(result.totalCount()).isEqualTo(5);
        assertThat(result.counts())
                .containsEntry("COLLECTED", 3L)
                .containsEntry("REPAIR_COMPLETED", 2L)
                .containsEntry("REPAIRING", 0L)
                .hasSize(7);
    }

    @Test
    void separatesClassifiedAndUnclassifiedRepairPriorities() {
        var period = period();
        when(statisticsMapper.countDamagesByRepairPriority(period.from(), period.to()))
                .thenReturn(List.of(
                        new StatisticsCountRow("HIGH", 2),
                        new StatisticsCountRow("URGENT", 1),
                        new StatisticsCountRow("UNCLASSIFIED", 3)
                ));

        var result = statisticsService.getRepairPriorityStatistics(period);

        assertThat(result.totalCount()).isEqualTo(6);
        assertThat(result.classifiedCount()).isEqualTo(3);
        assertThat(result.unclassifiedCount()).isEqualTo(3);
        assertThat(result.counts())
                .containsEntry("LOW", 0L)
                .containsEntry("NORMAL", 0L)
                .containsEntry("HIGH", 2L)
                .containsEntry("URGENT", 1L);
    }

    @Test
    void calculatesRepairCompletionRateFromCurrentStatus() {
        var period = period();
        when(statisticsMapper.countRepairCompletion(period.from(), period.to()))
                .thenReturn(new RepairCompletionCounts(38, 12, 4));

        var result = statisticsService.getRepairCompletionRate(period);

        assertThat(result.totalCount()).isEqualTo(38);
        assertThat(result.completedCount()).isEqualTo(12);
        assertThat(result.notRequiredCount()).isEqualTo(4);
        assertThat(result.completionRate()).isEqualByComparingTo("31.58");
    }

    @Test
    void returnsZeroCompletionRateWhenPeriodIsEmpty() {
        var period = period();
        when(statisticsMapper.countRepairCompletion(period.from(), period.to()))
                .thenReturn(new RepairCompletionCounts(0, 0, 0));

        assertThat(statisticsService.getRepairCompletionRate(period).completionRate())
                .isEqualByComparingTo("0.00");
    }

    private StatisticsPeriod period() {
        return new StatisticsPeriod(
                LocalDateTime.of(2026, 7, 1, 0, 0),
                LocalDateTime.of(2026, 8, 1, 0, 0)
        );
    }
}
