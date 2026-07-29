package com.blockai.roady.statistics.dto;

import com.blockai.roady.statistics.domain.RepairCompletionRate;

import java.math.BigDecimal;

public record RepairCompletionRateResponse(
        long totalCount,
        long completedCount,
        long notRequiredCount,
        BigDecimal completionRate
) {

    public static RepairCompletionRateResponse from(RepairCompletionRate statistics) {
        return new RepairCompletionRateResponse(
                statistics.totalCount(),
                statistics.completedCount(),
                statistics.notRequiredCount(),
                statistics.completionRate()
        );
    }
}
