package com.blockai.roady.statistics.domain;

import java.util.List;

public record DamageTimeSeries(
        StatisticsUnit unit,
        List<DamageTimeSeriesItem> items
) {

    public DamageTimeSeries {
        items = List.copyOf(items);
    }
}
