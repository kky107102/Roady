package com.blockai.roady.statistics.controller;

import com.blockai.roady.common.exception.GlobalExceptionHandler;
import com.blockai.roady.statistics.domain.DamageTimeSeries;
import com.blockai.roady.statistics.domain.DamageTimeSeriesItem;
import com.blockai.roady.statistics.service.StatisticsService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;
import java.util.List;

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
}
