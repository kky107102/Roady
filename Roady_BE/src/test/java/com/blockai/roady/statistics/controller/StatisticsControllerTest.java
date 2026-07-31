package com.blockai.roady.statistics.controller;

import com.blockai.roady.common.exception.GlobalExceptionHandler;
import com.blockai.roady.statistics.domain.DamageTimeSeries;
import com.blockai.roady.statistics.domain.DamageTimeSeriesItem;
import com.blockai.roady.statistics.domain.DamageStatusStatistics;
import com.blockai.roady.statistics.domain.RepairPriorityStatistics;
import com.blockai.roady.statistics.domain.RepairCompletionRate;
import com.blockai.roady.statistics.service.StatisticsService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import static com.blockai.roady.statistics.domain.StatisticsUnit.DAY;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class StatisticsControllerTest {

    private StatisticsService statisticsService;
    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        statisticsService = mock(StatisticsService.class);
        mockMvc = MockMvcBuilders.standaloneSetup(new StatisticsController(statisticsService))
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    void returnsDamageTimeSeries() throws Exception {
        when(statisticsService.getDamageTimeSeries(any(), any()))
                .thenReturn(new DamageTimeSeries(
                        DAY,
                        List.of(new DamageTimeSeriesItem(
                                "2026-07-01",
                                3,
                                1,
                                new BigDecimal("33.33")
                        ))
                ));

        mockMvc.perform(get("/api/statistics/damages/time-series")
                        .param("from", "2026-07-01T00:00:00")
                        .param("to", "2026-07-02T00:00:00")
                        .param("unit", "DAY"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.unit").value("DAY"))
                .andExpect(jsonPath("$.items[0].period").value("2026-07-01"))
                .andExpect(jsonPath("$.items[0].totalCount").value(3))
                .andExpect(jsonPath("$.items[0].repairCompletedCount").value(1))
                .andExpect(jsonPath("$.items[0].repairCompletionRate").value(33.33));
    }

    @Test
    void rejectsInvalidPeriod() throws Exception {
        mockMvc.perform(get("/api/statistics/damages/time-series")
                        .param("from", "2026-07-02T00:00:00")
                        .param("to", "2026-07-01T00:00:00")
                        .param("unit", "DAY"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value("from must be earlier than to."));
    }

    @Test
    void returnsDamageStatusStatistics() throws Exception {
        when(statisticsService.getDamageStatusStatistics(any()))
                .thenReturn(new DamageStatusStatistics(
                        5,
                        Map.of("COLLECTED", 3L, "REPAIR_COMPLETED", 2L)
                ));

        mockMvc.perform(get("/api/statistics/damages/by-status")
                        .param("from", "2026-07-01T00:00:00")
                        .param("to", "2026-08-01T00:00:00"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalCount").value(5))
                .andExpect(jsonPath("$.counts.COLLECTED").value(3))
                .andExpect(jsonPath("$.counts.REPAIR_COMPLETED").value(2));
    }

    @Test
    void returnsRepairPriorityStatistics() throws Exception {
        when(statisticsService.getRepairPriorityStatistics(any()))
                .thenReturn(new RepairPriorityStatistics(
                        6,
                        3,
                        3,
                        Map.of("LOW", 0L, "NORMAL", 0L, "HIGH", 2L, "URGENT", 1L)
                ));

        mockMvc.perform(get("/api/statistics/damages/by-repair-priority")
                        .param("from", "2026-07-01T00:00:00")
                        .param("to", "2026-08-01T00:00:00"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalCount").value(6))
                .andExpect(jsonPath("$.classifiedCount").value(3))
                .andExpect(jsonPath("$.unclassifiedCount").value(3))
                .andExpect(jsonPath("$.counts.URGENT").value(1));
    }

    @Test
    void returnsRepairCompletionRate() throws Exception {
        when(statisticsService.getRepairCompletionRate(any()))
                .thenReturn(new RepairCompletionRate(
                        38,
                        12,
                        4,
                        new BigDecimal("31.58")
                ));

        mockMvc.perform(get("/api/statistics/repair/completion-rate")
                        .param("from", "2026-07-01T00:00:00")
                        .param("to", "2026-08-01T00:00:00"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalCount").value(38))
                .andExpect(jsonPath("$.completedCount").value(12))
                .andExpect(jsonPath("$.canceledCount").value(4))
                .andExpect(jsonPath("$.completionRate").value(31.58));
    }
}
