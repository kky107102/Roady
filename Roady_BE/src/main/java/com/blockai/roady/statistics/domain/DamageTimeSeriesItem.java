package com.blockai.roady.statistics.domain;

import java.math.BigDecimal;

public record DamageTimeSeriesItem(
        String period,
        long totalCount,
        long repairCompletedCount,
        BigDecimal repairCompletionRate
) {
}
