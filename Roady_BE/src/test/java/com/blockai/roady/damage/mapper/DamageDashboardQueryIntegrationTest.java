package com.blockai.roady.damage.mapper;

import com.blockai.roady.damage.domain.DamageFilterCriteria;
import com.blockai.roady.damage.domain.DamageMapBounds;
import com.blockai.roady.damage.domain.DamageSearchCriteria;
import com.blockai.roady.damage.service.DamageService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@Transactional
class DamageDashboardQueryIntegrationTest {

    private static final LocalDateTime FROM = LocalDateTime.of(2099, 1, 1, 0, 0);
    private static final LocalDateTime TO = LocalDateTime.of(2099, 1, 2, 0, 0);

    @Autowired
    private DamageService damageService;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    private Long robotId;
    private Long assignedUserId;
    private Long olderDamageId;
    private Long newerDamageId;

    @BeforeEach
    void setUpDamageData() {
        assertDamageSchema();
        assertDamageIndexes();
        Long reportedBy = userId("admin");
        assignedUserId = userId("inspector");
        robotId = insertRobot(reportedBy);

        olderDamageId = insertDamage(
                reportedBy,
                assignedUserId,
                "REVIEW_REQUIRED",
                LocalDateTime.of(2099, 1, 1, 10, 0),
                true
        );
        newerDamageId = insertDamage(
                reportedBy,
                null,
                "REVIEW_REQUIRED",
                LocalDateTime.of(2099, 1, 1, 11, 0),
                false
        );
        insertDamage(
                reportedBy,
                null,
                "COLLECTED",
                LocalDateTime.of(2099, 1, 1, 12, 0),
                true
        );

        insertImage(olderDamageId, 1);
        insertImage(olderDamageId, 2);
        insertImage(newerDamageId, 1);
        insertAnalysis(
                olderDamageId,
                82,
                true,
                "URGENT",
                0.91,
                "SUCCESS",
                LocalDateTime.of(2099, 1, 1, 10, 10)
        );
        insertAnalysis(
                newerDamageId,
                55,
                true,
                "NORMAL",
                0.76,
                "SUCCESS",
                LocalDateTime.of(2099, 1, 1, 11, 10)
        );
        insertAnalysis(
                newerDamageId,
                null,
                null,
                null,
                null,
                "FAILED",
                LocalDateTime.of(2099, 1, 1, 11, 20)
        );
    }

    private void assertDamageSchema() {
        var columns = jdbcTemplate.queryForList(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = 'damages'
                """,
                String.class
        );
        assertThat(columns)
                .contains(
                        "id",
                        "robot_id",
                        "reported_by",
                        "assigned_to",
                        "description",
                        "address_name",
                        "road_address_name",
                        "region_code",
                        "region_1depth_name",
                        "region_2depth_name",
                        "region_3depth_name",
                        "geocoded_at",
                        "latitude",
                        "longitude",
                        "captured_at",
                        "current_status",
                        "created_at",
                        "updated_at"
                );
    }

    private void assertDamageIndexes() {
        var indexes = jdbcTemplate.queryForList(
                """
                SELECT DISTINCT index_name
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = 'damages'
                """,
                String.class
        );
        assertThat(indexes)
                .contains(
                        "idx_damages_created_at_id",
                        "idx_damages_status_created_at_id",
                        "idx_damages_robot_created_at",
                        "idx_damages_reported_by_created_at",
                        "idx_damages_assigned_to_created_at",
                        "idx_damages_address_name",
                        "idx_damages_road_address_name",
                        "idx_damages_region_code_created_at"
                );
    }

    @Test
    void searchExecutesPagedFilterQueryWithImageCounts() {
        var firstPage = damageService.search(new DamageSearchCriteria(
                FROM,
                TO,
                "REVIEW_REQUIRED",
                robotId,
                null,
                null,
                0,
                1
        ));

        assertThat(firstPage.content()).hasSize(1);
        assertThat(firstPage.content().getFirst().id()).isEqualTo(newerDamageId);
        assertThat(firstPage.content().getFirst().imageCount()).isEqualTo(1);
        assertThat(firstPage.content().getFirst().damageScore()).isEqualTo(55);
        assertThat(firstPage.content().getFirst().repairRequired()).isTrue();
        assertThat(firstPage.content().getFirst().repairPriority()).isEqualTo("NORMAL");
        assertThat(firstPage.content().getFirst().confidenceScore()).isEqualByComparingTo("0.7600");
        assertThat(firstPage.totalElements()).isEqualTo(2);
        assertThat(firstPage.totalPages()).isEqualTo(2);

        var secondPage = damageService.search(new DamageSearchCriteria(
                FROM,
                TO,
                "REVIEW_REQUIRED",
                robotId,
                null,
                null,
                1,
                1
        ));

        assertThat(secondPage.content()).hasSize(1);
        assertThat(secondPage.content().getFirst().id()).isEqualTo(olderDamageId);
        assertThat(secondPage.content().getFirst().imageCount()).isEqualTo(2);
        assertThat(secondPage.content().getFirst().damageScore()).isEqualTo(82);
        assertThat(secondPage.content().getFirst().repairPriority()).isEqualTo("URGENT");
    }

    @Test
    void searchFiltersByCaseNumberOrAddressKeyword() {
        var byCaseNumber = damageService.search(new DamageSearchCriteria(
                FROM,
                TO,
                null,
                null,
                null,
                newerDamageId.toString(),
                0,
                20
        ));

        assertThat(byCaseNumber.content())
                .extracting(damage -> damage.id())
                .containsExactly(newerDamageId);

        var byAddress = damageService.search(new DamageSearchCriteria(
                FROM,
                TO,
                "REVIEW_REQUIRED",
                null,
                null,
                "Juksan",
                0,
                20
        ));

        assertThat(byAddress.content())
                .extracting(damage -> damage.id())
                .containsExactly(newerDamageId, olderDamageId);
    }

    @Test
    void searchFiltersByRegionCodeAndPeriod() {
        var result = damageService.search(new DamageSearchCriteria(
                FROM,
                TO,
                null,
                null,
                null,
                "41550",
                null,
                0,
                20
        ));

        assertThat(result.content())
                .extracting(damage -> damage.id())
                .containsExactly(newerDamageId, olderDamageId);
    }

    @Test
    void summaryAndMarkersExecuteWithTheSameFilters() {
        var criteria = new DamageFilterCriteria(
                FROM,
                TO,
                "REVIEW_REQUIRED",
                robotId,
                null
        );

        jdbcTemplate.update(
                "UPDATE damages SET latitude = 35.1796, longitude = 129.0756 WHERE id = ?",
                newerDamageId
        );
        var bounds = new DamageMapBounds(
                new BigDecimal("37.45"),
                new BigDecimal("37.62"),
                new BigDecimal("126.80"),
                new BigDecimal("127.10")
        );

        var summary = damageService.summarize(criteria);
        var markers = damageService.findMapMarkers(criteria, bounds);

        assertThat(summary.total()).isEqualTo(2);
        assertThat(summary.unassigned()).isEqualTo(1);
        assertThat(summary.statusCounts())
                .containsEntry("REVIEW_REQUIRED", 2L)
                .containsEntry("COLLECTED", 0L);
        assertThat(markers)
                .extracting(marker -> marker.id())
                .containsExactly(olderDamageId);
    }

    private Long userId(String username) {
        return jdbcTemplate.queryForObject(
                "SELECT id FROM users WHERE username = ?",
                Long.class,
                username
        );
    }

    private Long insertRobot(Long userId) {
        String serialNumber = "dashboard-query-" + UUID.randomUUID();
        jdbcTemplate.update(
                """
                INSERT INTO robots (user_id, name, serial_number, status, active)
                VALUES (?, ?, ?, 'STANDBY', TRUE)
                """,
                userId,
                "Dashboard query test robot",
                serialNumber
        );
        return jdbcTemplate.queryForObject(
                "SELECT id FROM robots WHERE serial_number = ?",
                Long.class,
                serialNumber
        );
    }

    private Long insertDamage(
            Long reportedBy,
            Long assignedTo,
            String status,
            LocalDateTime createdAt,
            boolean hasCoordinates
    ) {
        String description = "dashboard-query-" + UUID.randomUUID();
        jdbcTemplate.update(
                """
                INSERT INTO damages (
                    robot_id,
                    reported_by,
                    assigned_to,
                    description,
                    address_name,
                    road_address_name,
                    region_code,
                    region_1depth_name,
                    region_2depth_name,
                    region_3depth_name,
                    geocoded_at,
                    latitude,
                    longitude,
                    captured_at,
                    current_status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                robotId,
                reportedBy,
                assignedTo,
                description,
                "Gyeonggi Anseong Juksan " + UUID.randomUUID(),
                "Gyeonggi Anseong Juksanchogyogil " + UUID.randomUUID(),
                status.equals("REVIEW_REQUIRED") ? "41550" : "41111",
                "Gyeonggi",
                "Anseong",
                "Juksan",
                createdAt,
                hasCoordinates ? 37.5665 : null,
                hasCoordinates ? 126.978 : null,
                createdAt,
                status,
                createdAt,
                createdAt
        );
        return jdbcTemplate.queryForObject(
                "SELECT id FROM damages WHERE description = ?",
                Long.class,
                description
        );
    }

    private void insertImage(Long damageId, int sortOrder) {
        jdbcTemplate.update(
                """
                INSERT INTO damage_images (
                    damage_id,
                    sort_order,
                    original_filename,
                    content_type,
                    size_bytes,
                    data
                )
                VALUES (?, ?, ?, 'image/jpeg', 1, ?)
                """,
                damageId,
                sortOrder,
                "image-" + sortOrder + ".jpg",
                new byte[]{1}
        );
    }

    private void insertAnalysis(
            Long damageId,
            Integer damageScore,
            Boolean repairRequired,
            String repairPriority,
            Double confidenceScore,
            String analysisStatus,
            LocalDateTime createdAt
    ) {
        jdbcTemplate.update(
                """
                INSERT INTO damage_ai_analysis_results (
                    damage_id,
                    damaged,
                    damage_score,
                    repair_required,
                    repair_priority,
                    confidence_score,
                    analysis_status,
                    analyzed_at,
                    created_at
                )
                VALUES (?, TRUE, ?, ?, ?, ?, ?, ?, ?)
                """,
                damageId,
                damageScore,
                repairRequired,
                repairPriority,
                confidenceScore,
                analysisStatus,
                createdAt,
                createdAt
        );
    }
}
