package com.blockai.roady.statistics.controller;

import com.blockai.roady.statistics.domain.StatisticsPeriod;
import com.blockai.roady.statistics.domain.StatisticsUnit;
import com.blockai.roady.statistics.dto.DamageTimeSeriesResponse;
import com.blockai.roady.statistics.dto.DamageStatusStatisticsResponse;
import com.blockai.roady.statistics.dto.RepairPriorityStatisticsResponse;
import com.blockai.roady.statistics.dto.RepairCompletionRateResponse;
import com.blockai.roady.statistics.service.StatisticsService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/statistics")
public class StatisticsController {

    private final StatisticsService statisticsService;

    public StatisticsController(StatisticsService statisticsService) {
        this.statisticsService = statisticsService;
    }

    @GetMapping("/damages/time-series")
    public DamageTimeSeriesResponse getDamageTimeSeries(
            @RequestParam("from")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime from,
            @RequestParam("to")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime to,
            @RequestParam("unit") String unit
    ) {
        var period = new StatisticsPeriod(from, to);
        return DamageTimeSeriesResponse.from(
                statisticsService.getDamageTimeSeries(period, StatisticsUnit.from(unit))
        );
    }

    @GetMapping("/damages/by-status")
    public DamageStatusStatisticsResponse getDamageStatusStatistics(
            @RequestParam("from")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime from,
            @RequestParam("to")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime to
    ) {
        return DamageStatusStatisticsResponse.from(
                statisticsService.getDamageStatusStatistics(new StatisticsPeriod(from, to))
        );
    }

    @GetMapping("/damages/by-repair-priority")
    public RepairPriorityStatisticsResponse getRepairPriorityStatistics(
            @RequestParam("from")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime from,
            @RequestParam("to")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime to
    ) {
        return RepairPriorityStatisticsResponse.from(
                statisticsService.getRepairPriorityStatistics(new StatisticsPeriod(from, to))
        );
    }

    @GetMapping("/repair/completion-rate")
    public RepairCompletionRateResponse getRepairCompletionRate(
            @RequestParam("from")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime from,
            @RequestParam("to")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime to
    ) {
        return RepairCompletionRateResponse.from(
                statisticsService.getRepairCompletionRate(new StatisticsPeriod(from, to))
        );
    }
}
