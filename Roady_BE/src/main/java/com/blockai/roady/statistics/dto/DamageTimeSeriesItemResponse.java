package com.blockai.roady.statistics.dto;

import com.blockai.roady.statistics.domain.DamageTimeSeriesItem;

import java.math.BigDecimal;

public record DamageTimeSeriesItemResponse(
        String period,
        long totalCount,
        long repairCompletedCount,
        BigDecimal repairCompletionRate
) {

    public static DamageTimeSeriesItemResponse from(DamageTimeSeriesItem item) {
        return new DamageTimeSeriesItemResponse(
                item.period(),
                item.totalCount(),
                item.repairCompletedCount(),
                item.repairCompletionRate()
        );
    }
}
