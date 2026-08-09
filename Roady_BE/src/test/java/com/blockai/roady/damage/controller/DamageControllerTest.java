package com.blockai.roady.damage.controller;

import com.blockai.roady.common.exception.GlobalExceptionHandler;
import com.blockai.roady.damage.domain.DamageMapMarker;
import com.blockai.roady.damage.domain.DamageSearchCriteria;
import com.blockai.roady.damage.domain.DamageSearchItem;
import com.blockai.roady.damage.domain.DamageSearchPage;
import com.blockai.roady.damage.domain.DamageSummary;
import com.blockai.roady.damage.service.DamageAiAnalysisService;
import com.blockai.roady.damage.service.DamageService;
import com.blockai.roady.robot.domain.Robot;
import com.blockai.roady.robot.domain.RobotStatus;
import com.blockai.roady.robot.service.RobotService;
import com.blockai.roady.security.AuthenticatedUser;
import com.blockai.roady.user.domain.UserRole;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.method.annotation.AuthenticationPrincipalArgumentResolver;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class DamageControllerTest {

    private DamageService damageService;
    private DamageAiAnalysisService aiAnalysisService;
    private RobotService robotService;
    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        damageService = mock(DamageService.class);
        aiAnalysisService = mock(DamageAiAnalysisService.class);
        robotService = mock(RobotService.class);
        DamageController controller = new DamageController(damageService, aiAnalysisService, robotService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller)
                .setCustomArgumentResolvers(new AuthenticationPrincipalArgumentResolver())
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    void createDamageWithoutTokenUsesRobotUserIdAsReporter() throws Exception {
        MockMultipartFile image = new MockMultipartFile(
                "images",
                "damage.jpg",
                "image/jpeg",
                new byte[]{1, 2, 3}
        );
        LocalDateTime capturedAt = LocalDateTime.of(2026, 7, 22, 14, 30);
        when(robotService.get(10L)).thenReturn(new Robot(
                10L,
                2L,
                "Inspection Robot",
                "RB-001",
                RobotStatus.STANDBY,
                true,
                capturedAt,
                capturedAt
        ));
        when(damageService.create(
                eq(10L),
                eq(2L),
                eq(null),
                eq("tactile block crack"),
                eq(new BigDecimal("37.5665000")),
                eq(new BigDecimal("126.9780000")),
                eq(capturedAt),
                any()
        )).thenReturn(new DamageSummary(
                1L,
                10L,
                2L,
                null,
                "tactile block crack",
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                new BigDecimal("37.5665000"),
                new BigDecimal("126.9780000"),
                capturedAt,
                "COLLECTED",
                null,
                null,
                null,
                1L,
                capturedAt,
                capturedAt
        ));
        when(damageService.getImageMetadata(1L)).thenReturn(List.of());
        when(damageService.getSummary(1L)).thenReturn(new DamageSummary(
                1L,
                10L,
                2L,
                null,
                "tactile block crack",
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                new BigDecimal("37.5665000"),
                new BigDecimal("126.9780000"),
                capturedAt,
                "AI_ANALYZING",
                null,
                null,
                null,
                1L,
                capturedAt,
                capturedAt
        ));

        mockMvc.perform(multipart("/api/damages")
                        .file(image)
                        .param("robotId", "10")
                        .param("description", "tactile block crack")
                        .param("latitude", "37.5665000")
                        .param("longitude", "126.9780000")
                        .param("capturedAt", "2026-07-22T14:30:00"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.robotId").value(10))
                .andExpect(jsonPath("$.reportedBy").value(2))
                .andExpect(jsonPath("$.currentStatus").value("AI_ANALYZING"));

        verify(robotService).get(10L);
        verify(aiAnalysisService).createAndEnqueue(1L);
        verify(damageService).getSummary(1L);
    }

    @Test
    void createDamageWithoutTokenRequiresRobotId() throws Exception {
        MockMultipartFile image = new MockMultipartFile(
                "images",
                "damage.jpg",
                "image/jpeg",
                new byte[]{1, 2, 3}
        );

        mockMvc.perform(multipart("/api/damages").file(image))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message")
                        .value("robotId is required for unauthenticated robot damage uploads."));
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
                "URGENT",
                "CRACK",
                "review note",
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
                .andExpect(jsonPath("$.content[0].processingPriority").value("URGENT"))
                .andExpect(jsonPath("$.content[0].reviewDamageType").value("CRACK"))
                .andExpect(jsonPath("$.content[0].reviewNote").value("review note"))
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
    void updateDamageReviewChangesStatusAndProcessingPriority() throws Exception {
        LocalDateTime updatedAt = LocalDateTime.of(2026, 7, 31, 11, 0);
        when(damageService.updateReview(
                eq(1L),
                eq("REQUESTED"),
                eq("URGENT"),
                eq("LARGE_MISSING"),
                eq("현장 확인 필요")
        ))
                .thenReturn(new DamageSummary(
                        1L,
                        10L,
                        2L,
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
                        "REQUESTED",
                        "URGENT",
                        "LARGE_MISSING",
                        "현장 확인 필요",
                        2L,
                        updatedAt,
                        updatedAt
                ));

        mockMvc.perform(patch("/api/damages/{damageId}/review", 1L)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "status": "REQUESTED",
                                  "processingPriority": "URGENT",
                                  "reviewDamageType": "LARGE_MISSING",
                                  "reviewNote": "현장 확인 필요"
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.currentStatus").value("REQUESTED"))
                .andExpect(jsonPath("$.processingPriority").value("URGENT"))
                .andExpect(jsonPath("$.reviewDamageType").value("LARGE_MISSING"))
                .andExpect(jsonPath("$.reviewNote").value("현장 확인 필요"));
    }

    @Test
    void updateDamageReviewRejectsInvalidStatus() throws Exception {
        when(damageService.updateReview(eq(1L), eq("REPAIR_COMPLETED"), eq(null), eq(null), eq(null)))
                .thenThrow(new IllegalArgumentException("Invalid damage review status."));

        mockMvc.perform(patch("/api/damages/{damageId}/review", 1L)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "status": "REPAIR_COMPLETED"
                                }
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value("Invalid damage review status."));
    }

    @Test
    void createDamageRepairRequestPassesNoteAndReturnsUpdatedStatus() throws Exception {
        LocalDateTime updatedAt = LocalDateTime.of(2026, 8, 4, 15, 0);
        AuthenticatedUser principal = new AuthenticatedUser(2L, "inspector", UserRole.INSPECTOR);
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(
                principal,
                null,
                List.of(new SimpleGrantedAuthority("ROLE_INSPECTOR"))
        ));
        when(damageService.requestRepair(3L, 2L, "HIGH", "CRACK", 9L, "hello"))
                .thenReturn(new DamageSummary(
                        3L,
                        10L,
                        2L,
                        null,
                        "tactile block crack",
                        null,
                        null,
                        null,
                        null,
                        null,
                        null,
                        null,
                        BigDecimal.valueOf(37.5665),
                        BigDecimal.valueOf(126.978),
                        LocalDateTime.of(2026, 8, 4, 14, 0),
                        "REPAIR_IN_PROGRESS",
                        "HIGH",
                        "CRACK",
                        "reviewed",
                        1L,
                        updatedAt,
                        updatedAt
                ));

        try {
            mockMvc.perform(post("/api/damages/{damageId}/repair-request", 3L)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                      "processingPriority": "HIGH",
                                      "reviewDamageType": "CRACK",
                                      "repairerId": 9,
                                      "note": "hello"
                                    }
                                    """))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.id").value(3))
                    .andExpect(jsonPath("$.currentStatus").value("REPAIR_IN_PROGRESS"));
        } finally {
            SecurityContextHolder.clearContext();
        }

        verify(damageService).requestRepair(3L, 2L, "HIGH", "CRACK", 9L, "hello");
    }

    @Test
    void updateDamageRepairRequestPassesEditableFieldsAndKeepsStatus() throws Exception {
        LocalDateTime updatedAt = LocalDateTime.of(2026, 8, 4, 15, 30);
        AuthenticatedUser principal = new AuthenticatedUser(2L, "inspector", UserRole.INSPECTOR);
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(
                principal,
                null,
                List.of(new SimpleGrantedAuthority("ROLE_INSPECTOR"))
        ));
        when(damageService.updateRepairRequest(3L, 2L, "URGENT", "LARGE_MISSING", 9L, "changed"))
                .thenReturn(new DamageSummary(
                        3L,
                        10L,
                        2L,
                        null,
                        "tactile block crack",
                        null,
                        null,
                        null,
                        null,
                        null,
                        null,
                        null,
                        BigDecimal.valueOf(37.5665),
                        BigDecimal.valueOf(126.978),
                        LocalDateTime.of(2026, 8, 4, 14, 0),
                        "REPAIR_IN_PROGRESS",
                        "URGENT",
                        "LARGE_MISSING",
                        "reviewed",
                        1L,
                        updatedAt,
                        updatedAt
                ));

        try {
            mockMvc.perform(patch("/api/damages/{damageId}/repair-request", 3L)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                      "processingPriority": "URGENT",
                                      "reviewDamageType": "LARGE_MISSING",
                                      "repairerId": 9,
                                      "note": "changed"
                                    }
                                    """))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.id").value(3))
                    .andExpect(jsonPath("$.currentStatus").value("REPAIR_IN_PROGRESS"));
        } finally {
            SecurityContextHolder.clearContext();
        }

        verify(damageService).updateRepairRequest(3L, 2L, "URGENT", "LARGE_MISSING", 9L, "changed");
    }

    @Test
    void completeDamageRepairPassesNoteAndReturnsUpdatedStatus() throws Exception {
        LocalDateTime updatedAt = LocalDateTime.of(2026, 8, 4, 16, 0);
        AuthenticatedUser principal = new AuthenticatedUser(2L, "inspector", UserRole.INSPECTOR);
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(
                principal,
                null,
                List.of(new SimpleGrantedAuthority("ROLE_INSPECTOR"))
        ));
        when(damageService.completeRepair(3L, 2L, LocalDate.of(2026, 8, 4), "done"))
                .thenReturn(new DamageSummary(
                        3L,
                        10L,
                        2L,
                        null,
                        "tactile block crack",
                        null,
                        null,
                        null,
                        null,
                        null,
                        null,
                        null,
                        BigDecimal.valueOf(37.5665),
                        BigDecimal.valueOf(126.978),
                        LocalDateTime.of(2026, 8, 4, 14, 0),
                        "REPAIR_COMPLETED",
                        "HIGH",
                        "CRACK",
                        "reviewed",
                        1L,
                        updatedAt,
                        updatedAt
                ));

        try {
            mockMvc.perform(patch("/api/damages/{damageId}/repair-complete", 3L)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                      "completedAt": "2026-08-04",
                                      "note": "done"
                                    }
                                    """))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.id").value(3))
                    .andExpect(jsonPath("$.currentStatus").value("REPAIR_COMPLETED"));
        } finally {
            SecurityContextHolder.clearContext();
        }

        verify(damageService).completeRepair(3L, 2L, LocalDate.of(2026, 8, 4), "done");
    }

    @Test
    void cancelDamageRepairPassesNoteAndReturnsUpdatedStatus() throws Exception {
        LocalDateTime updatedAt = LocalDateTime.of(2026, 8, 4, 16, 0);
        AuthenticatedUser principal = new AuthenticatedUser(2L, "inspector", UserRole.INSPECTOR);
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(
                principal,
                null,
                List.of(new SimpleGrantedAuthority("ROLE_INSPECTOR"))
        ));
        when(damageService.cancelRepair(3L, 2L, "cancel"))
                .thenReturn(new DamageSummary(
                        3L,
                        10L,
                        2L,
                        null,
                        "tactile block crack",
                        null,
                        null,
                        null,
                        null,
                        null,
                        null,
                        null,
                        BigDecimal.valueOf(37.5665),
                        BigDecimal.valueOf(126.978),
                        LocalDateTime.of(2026, 8, 4, 14, 0),
                        "REQUESTED",
                        "HIGH",
                        "CRACK",
                        "reviewed",
                        1L,
                        updatedAt,
                        updatedAt
                ));

        try {
            mockMvc.perform(patch("/api/damages/{damageId}/repair-cancel", 3L)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                      "note": "cancel"
                                    }
                                    """))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.id").value(3))
                    .andExpect(jsonPath("$.currentStatus").value("REQUESTED"));
        } finally {
            SecurityContextHolder.clearContext();
        }

        verify(damageService).cancelRepair(3L, 2L, "cancel");
    }
}
