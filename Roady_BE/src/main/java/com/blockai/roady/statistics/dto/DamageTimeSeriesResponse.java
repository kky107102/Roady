package com.blockai.roady.statistics.dto;

import com.blockai.roady.statistics.domain.DamageTimeSeries;

import java.util.List;

public record DamageTimeSeriesResponse(
        String unit,
        List<DamageTimeSeriesItemResponse> items
) {

    public static DamageTimeSeriesResponse from(DamageTimeSeries timeSeries) {
        return new DamageTimeSeriesResponse(
                timeSeries.unit().name(),
                timeSeries.items().stream()
                        .map(DamageTimeSeriesItemResponse::from)
                        .toList()
        );
    }
}
