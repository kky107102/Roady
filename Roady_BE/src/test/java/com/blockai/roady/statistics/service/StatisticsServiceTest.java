package com.blockai.roady.statistics.service;

import com.blockai.roady.statistics.domain.DamageTimeSeriesRow;
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
}
