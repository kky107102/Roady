package com.blockai.roady.damage.controller;

import com.blockai.roady.common.exception.GlobalExceptionHandler;
import com.blockai.roady.damage.domain.DamageSearchCriteria;
import com.blockai.roady.damage.domain.DamageSearchItem;
import com.blockai.roady.damage.domain.DamageSearchPage;
import com.blockai.roady.damage.domain.DamageMapMarker;
import com.blockai.roady.damage.service.DamageAiAnalysisService;
import com.blockai.roady.damage.service.DamageService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class DamageControllerTest {

    private DamageService damageService;
    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        damageService = mock(DamageService.class);
        DamageAiAnalysisService aiAnalysisService = mock(DamageAiAnalysisService.class);
        DamageController controller = new DamageController(damageService, aiAnalysisService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller)
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    void getDamagesReturnsPagedSearchResponse() throws Exception {
        LocalDateTime createdAt = LocalDateTime.of(2026, 7, 22, 14, 30, 1);
        DamageSearchItem summary = new DamageSearchItem(
                1L,
                10L,
                5L,
                "점자블록 균열",
                BigDecimal.valueOf(37.5665),
                BigDecimal.valueOf(126.978),
                LocalDateTime.of(2026, 7, 22, 14, 30),
                "REVIEW_REQUIRED",
                2L,
                82,
                true,
                "URGENT",
                BigDecimal.valueOf(0.91),
                createdAt
        );
        when(damageService.search(any(DamageSearchCriteria.class)))
                .thenReturn(new DamageSearchPage(List.of(summary), 0, 20, 1, 1));

        mockMvc.perform(get("/api/damages"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].id").value(1))
                .andExpect(jsonPath("$.content[0].assignedTo").value(5))
                .andExpect(jsonPath("$.content[0].currentStatus").value("REVIEW_REQUIRED"))
                .andExpect(jsonPath("$.content[0].imageCount").value(2))
                .andExpect(jsonPath("$.content[0].damageScore").value(82))
                .andExpect(jsonPath("$.content[0].repairRequired").value(true))
                .andExpect(jsonPath("$.content[0].repairPriority").value("URGENT"))
                .andExpect(jsonPath("$.content[0].confidenceScore").value(0.91))
                .andExpect(jsonPath("$.content[0].reportedBy").doesNotExist())
                .andExpect(jsonPath("$.content[0].updatedAt").doesNotExist())
                .andExpect(jsonPath("$.page").value(0))
                .andExpect(jsonPath("$.size").value(20))
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.totalPages").value(1));
    }

    @Test
    void getDamagesRejectsInvalidPageSize() throws Exception {
        mockMvc.perform(get("/api/damages").param("size", "101"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value("size must be between 1 and 100."));
    }

    @Test
    void getMapMarkersReturnsOnlyMapFields() throws Exception {
        when(damageService.findMapMarkers(any()))
                .thenReturn(List.of(new DamageMapMarker(
                        1L,
                        BigDecimal.valueOf(37.5665),
                        BigDecimal.valueOf(126.978),
                        "REVIEW_REQUIRED"
                )));

        mockMvc.perform(get("/api/damages/map-markers")
                        .param("status", "REVIEW_REQUIRED"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(1))
                .andExpect(jsonPath("$[0].latitude").value(37.5665))
                .andExpect(jsonPath("$[0].longitude").value(126.978))
                .andExpect(jsonPath("$[0].currentStatus").value("REVIEW_REQUIRED"))
                .andExpect(jsonPath("$[0].description").doesNotExist())
                .andExpect(jsonPath("$[0].assignedTo").doesNotExist());
    }
}
