package com.blockai.roady.statistics.domain;

import java.math.BigDecimal;

public record RepairCompletionRate(
        long totalCount,
        long completedCount,
        long notRequiredCount,
        BigDecimal completionRate
) {
}
