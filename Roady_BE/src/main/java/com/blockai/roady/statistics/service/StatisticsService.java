package com.blockai.roady.statistics.service;

import com.blockai.roady.statistics.domain.DamageTimeSeries;
import com.blockai.roady.statistics.domain.DamageTimeSeriesItem;
import com.blockai.roady.statistics.domain.DamageTimeSeriesRow;
import com.blockai.roady.statistics.domain.StatisticsPeriod;
import com.blockai.roady.statistics.domain.StatisticsUnit;
import com.blockai.roady.statistics.mapper.StatisticsMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class StatisticsService {

    private static final int RATE_SCALE = 2;

    private final StatisticsMapper statisticsMapper;

    public StatisticsService(StatisticsMapper statisticsMapper) {
        this.statisticsMapper = statisticsMapper;
    }

    @Transactional(readOnly = true)
    public DamageTimeSeries getDamageTimeSeries(StatisticsPeriod period, StatisticsUnit unit) {
        Map<String, DamageTimeSeriesRow> rowsByPeriod = statisticsMapper.findDamageTimeSeries(
                        period.from(),
                        period.to(),
                        unit.name()
                ).stream()
                .collect(Collectors.toMap(DamageTimeSeriesRow::period, Function.identity()));

        var items = new ArrayList<DamageTimeSeriesItem>();
        for (
                var cursor = unit.floor(period.from());
                cursor.isBefore(period.to());
                cursor = unit.next(cursor)
        ) {
            String periodKey = unit.format(cursor);
            DamageTimeSeriesRow row = rowsByPeriod.get(periodKey);
            long totalCount = row == null ? 0 : row.totalCount();
            long completedCount = row == null ? 0 : row.repairCompletedCount();
            items.add(new DamageTimeSeriesItem(
                    periodKey,
                    totalCount,
                    completedCount,
                    percentage(completedCount, totalCount)
            ));
        }
        return new DamageTimeSeries(unit, items);
    }

    private BigDecimal percentage(long numerator, long denominator) {
        if (denominator == 0) {
            return BigDecimal.ZERO.setScale(RATE_SCALE);
        }
        return BigDecimal.valueOf(numerator)
                .multiply(BigDecimal.valueOf(100))
                .divide(BigDecimal.valueOf(denominator), RATE_SCALE, RoundingMode.HALF_UP);
    }
}
