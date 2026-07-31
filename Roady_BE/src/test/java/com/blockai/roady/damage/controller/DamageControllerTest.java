package com.blockai.roady.damage.controller;

import com.blockai.roady.common.exception.GlobalExceptionHandler;
import com.blockai.roady.damage.domain.DamageMapMarker;
import com.blockai.roady.damage.domain.DamageSearchCriteria;
import com.blockai.roady.damage.domain.DamageSearchItem;
import com.blockai.roady.damage.domain.DamageSearchPage;
import com.blockai.roady.damage.domain.DamageStatus;
import com.blockai.roady.damage.service.DamageAiAnalysisService;
import com.blockai.roady.damage.service.DamageService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
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
                "tactile block crack",
                "Gyeonggi Anseong Juksan 343-1",
                "Gyeonggi Anseong Juksanchogyogil 69-4",
                "41550",
                "Gyeonggi",
                "Anseong",
                "Juksan",
                LocalDateTime.of(2026, 7, 22, 14, 31),
                BigDecimal.valueOf(37.5665),
                BigDecimal.valueOf(126.978),
                LocalDateTime.of(2026, 7, 22, 14, 30),
                "AI_ANALYZED",
                2L,
                82,
                "CRACK",
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
                .andExpect(jsonPath("$.content[0].addressName").value("Gyeonggi Anseong Juksan 343-1"))
                .andExpect(jsonPath("$.content[0].roadAddressName").value("Gyeonggi Anseong Juksanchogyogil 69-4"))
                .andExpect(jsonPath("$.content[0].regionCode").value("41550"))
                .andExpect(jsonPath("$.content[0].region1DepthName").value("Gyeonggi"))
                .andExpect(jsonPath("$.content[0].currentStatus").value("AI_ANALYZED"))
                .andExpect(jsonPath("$.content[0].imageCount").value(2))
                .andExpect(jsonPath("$.content[0].damageScore").value(82))
                .andExpect(jsonPath("$.content[0].damageType").value("CRACK"))
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
    void getDamagesAcceptsKeywordForCaseNumberOrAddressSearch() throws Exception {
        ArgumentCaptor<DamageSearchCriteria> criteriaCaptor = ArgumentCaptor.forClass(DamageSearchCriteria.class);
        when(damageService.search(criteriaCaptor.capture()))
                .thenReturn(new DamageSearchPage(List.of(), 0, 20, 0, 0));

        mockMvc.perform(get("/api/damages").param("keyword", "Juksan"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray());

        assertThat(criteriaCaptor.getValue().keyword()).isEqualTo("Juksan");
    }

    @Test
    void getDamagesAcceptsRegionCodeWithPeriodFilter() throws Exception {
        ArgumentCaptor<DamageSearchCriteria> criteriaCaptor = ArgumentCaptor.forClass(DamageSearchCriteria.class);
        when(damageService.search(criteriaCaptor.capture()))
                .thenReturn(new DamageSearchPage(List.of(), 0, 20, 0, 0));

        mockMvc.perform(get("/api/damages")
                        .param("regionCode", "41550")
                        .param("from", "2026-07-01T00:00:00")
                        .param("to", "2026-08-01T00:00:00"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray());

        assertThat(criteriaCaptor.getValue().regionCode()).isEqualTo("41550");
        assertThat(criteriaCaptor.getValue().from()).isEqualTo(LocalDateTime.of(2026, 7, 1, 0, 0));
        assertThat(criteriaCaptor.getValue().to()).isEqualTo(LocalDateTime.of(2026, 8, 1, 0, 0));
    }

    @Test
    void getDamagesRejectsInvalidPageSize() throws Exception {
        mockMvc.perform(get("/api/damages").param("size", "101"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value("size must be between 1 and 100."));
    }

    @Test
    void getMapMarkersReturnsOnlyMapFields() throws Exception {
        when(damageService.findMapMarkers(any(), any()))
                .thenReturn(List.of(new DamageMapMarker(
                        1L,
                        BigDecimal.valueOf(37.5665),
                        BigDecimal.valueOf(126.978),
                        "AI_ANALYZED"
                )));

        mockMvc.perform(get("/api/damages/map-markers")
                        .param("status", "AI_ANALYZED")
                        .param("south", "37.45")
                        .param("north", "37.62")
                        .param("west", "126.80")
                        .param("east", "127.10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(1))
                .andExpect(jsonPath("$[0].latitude").value(37.5665))
                .andExpect(jsonPath("$[0].longitude").value(126.978))
                .andExpect(jsonPath("$[0].currentStatus").value("AI_ANALYZED"))
                .andExpect(jsonPath("$[0].description").doesNotExist())
                .andExpect(jsonPath("$[0].assignedTo").doesNotExist());
    }

    @Test
    void getMapMarkersRejectsInvalidBounds() throws Exception {
        mockMvc.perform(get("/api/damages/map-markers")
                        .param("south", "37.62")
                        .param("north", "37.45")
                        .param("west", "126.80")
                        .param("east", "127.10"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value("south must be less than north."));
    }

    @Test
    void getMapMarkersRequiresBounds() throws Exception {
        mockMvc.perform(get("/api/damages/map-markers"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void updateDamageStatusAppliesAdministratorVerdict() throws Exception {
        mockMvc.perform(patch("/api/damages/1/status")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "status": "REQUESTED",
                                  "comment": "Administrator verdict: repair required"
                                }
                                """))
                .andExpect(status().isNoContent());

        verify(damageService).updateReviewStatus(1L, DamageStatus.REQUESTED);
    }

    @Test
    void updateDamageStatusRejectsMissingStatus() throws Exception {
        mockMvc.perform(patch("/api/damages/1/status")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isBadRequest());
    }
}
