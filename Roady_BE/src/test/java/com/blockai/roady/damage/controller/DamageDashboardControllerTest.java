package com.blockai.roady.damage.controller;

import com.blockai.roady.common.exception.GlobalExceptionHandler;
import com.blockai.roady.damage.domain.DamageDashboardSummary;
import com.blockai.roady.damage.domain.DamageFilterCriteria;
import com.blockai.roady.damage.service.DamageService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.LinkedHashMap;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class DamageDashboardControllerTest {

    private DamageService damageService;
    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        damageService = mock(DamageService.class);
        DamageDashboardController controller = new DamageDashboardController(damageService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller)
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    void getSummaryReturnsDashboardDamageCounts() throws Exception {
        var statusCounts = new LinkedHashMap<String, Long>();
        statusCounts.put("COLLECTED", 20L);
        statusCounts.put("AI_ANALYZING", 12L);
        statusCounts.put("AI_ANALYZED", 23L);
        statusCounts.put("REQUESTED", 18L);
        statusCounts.put("REPAIR_SCHEDULED", 10L);
        statusCounts.put("REPAIR_IN_PROGRESS", 8L);
        statusCounts.put("REPAIR_COMPLETED", 27L);
        statusCounts.put("CANCELED", 5L);
        when(damageService.summarize(any(DamageFilterCriteria.class)))
                .thenReturn(new DamageDashboardSummary(123, 12, statusCounts));

        mockMvc.perform(get("/api/dashboard/damages/summary")
                        .param("from", "2026-07-01T00:00:00")
                        .param("to", "2026-08-01T00:00:00")
                        .param("robotId", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total").value(123))
                .andExpect(jsonPath("$.unassigned").value(12))
                .andExpect(jsonPath("$.statusCounts.COLLECTED").value(20))
                .andExpect(jsonPath("$.statusCounts.AI_ANALYZING").value(12))
                .andExpect(jsonPath("$.statusCounts.AI_ANALYZED").value(23))
                .andExpect(jsonPath("$.statusCounts.REQUESTED").value(18))
                .andExpect(jsonPath("$.statusCounts.REPAIR_COMPLETED").value(27));
    }

    @Test
    void getSummaryRejectsInvalidStatus() throws Exception {
        mockMvc.perform(get("/api/dashboard/damages/summary")
                        .param("status", "UNKNOWN"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value("Invalid damage status."));
    }
}
