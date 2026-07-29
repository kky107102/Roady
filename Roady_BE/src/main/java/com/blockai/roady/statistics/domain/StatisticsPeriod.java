package com.blockai.roady.statistics.domain;

import java.time.LocalDateTime;

public record StatisticsPeriod(
        LocalDateTime from,
        LocalDateTime to
) {

    public StatisticsPeriod {
        if (from == null || to == null) {
            throw new IllegalArgumentException("from and to are required.");
        }
        if (!from.isBefore(to)) {
            throw new IllegalArgumentException("from must be earlier than to.");
        }
    }
}
