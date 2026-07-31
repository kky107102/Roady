package com.blockai.roady.config;

import com.blockai.roady.user.domain.UserAccount;
import com.blockai.roady.user.domain.UserRole;
import com.blockai.roady.user.service.UserAccountService;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Profile;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Base64;

@Component
@Profile("!inmemory")
@ConditionalOnProperty(prefix = "roady.sample-data", name = "enabled", havingValue = "true", matchIfMissing = true)
public class SampleDataInitializer implements ApplicationRunner {

    private static final byte[] SAMPLE_PNG = Base64.getDecoder().decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
    );

    private final UserAccountService userAccountService;
    private final JdbcTemplate jdbcTemplate;

    public SampleDataInitializer(UserAccountService userAccountService, JdbcTemplate jdbcTemplate) {
        this.userAccountService = userAccountService;
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public void run(ApplicationArguments args) {
        UserAccount inspector = ensureUser(
                "inspector",
                "inspector1234",
                "inspector@roady.local",
                "Roady Inspector",
                UserRole.INSPECTOR
        );
        UserAccount repairer = ensureUser(
                "repairer",
                "repairer1234",
                "repairer@roady.local",
                "Roady Repairer",
                UserRole.REPAIRER
        );

        Long alphaRobotId = seedRobot(inspector.id(), "Roady Alpha", "RDY-SAMPLE-001", "MOVING");
        Long betaRobotId = seedRobot(inspector.id(), "Roady Beta", "RDY-SAMPLE-002", "INSPECTING");

        seedDamage(new DamageSeed(
                alphaRobotId,
                inspector.id(),
                repairer.id(),
                "Sample crack on Teheran-ro bus lane",
                "Seoul Gangnam-gu Yeoksam-dong 737",
                "Seoul Gangnam-gu Teheran-ro 212",
                "11680",
                "Seoul",
                "Gangnam-gu",
                "Yeoksam-dong",
                new BigDecimal("37.5006130"),
                new BigDecimal("127.0364310"),
                LocalDateTime.of(2026, 7, 27, 9, 30),
                "AI_ANALYZED",
                "URGENT",
                88,
                "CRACK",
                true,
                "URGENT",
                new BigDecimal("0.9300")
        ));
        seedDamage(new DamageSeed(
                alphaRobotId,
                inspector.id(),
                repairer.id(),
                "Sample pothole near Suwon city hall",
                "Gyeonggi Suwon-si Paldal-gu Ingye-dong 1111",
                "Gyeonggi Suwon-si Paldal-gu Hyowon-ro 241",
                "41115",
                "Gyeonggi-do",
                "Suwon-si Paldal-gu",
                "Ingye-dong",
                new BigDecimal("37.2635730"),
                new BigDecimal("127.0286010"),
                LocalDateTime.of(2026, 7, 28, 14, 15),
                "REPAIR_IN_PROGRESS",
                "HIGH",
                76,
                "BREAKAGE",
                true,
                "HIGH",
                new BigDecimal("0.8700")
        ));
        seedDamage(new DamageSeed(
                betaRobotId,
                inspector.id(),
                repairer.id(),
                "Sample worn lane marking near Anyang stream",
                "Gyeonggi Anyang-si Dongan-gu Bisan-dong 1100",
                "Gyeonggi Anyang-si Dongan-gu Simin-daero 235",
                "41173",
                "Gyeonggi-do",
                "Anyang-si Dongan-gu",
                "Bisan-dong",
                new BigDecimal("37.3942870"),
                new BigDecimal("126.9567530"),
                LocalDateTime.of(2026, 7, 29, 10, 5),
                "REPAIR_COMPLETED",
                "NORMAL",
                42,
                "WEAR",
                true,
                "NORMAL",
                new BigDecimal("0.8100")
        ));
        seedDamage(new DamageSeed(
                null,
                inspector.id(),
                null,
                "Sample shallow surface scratch in Seongnam",
                "Gyeonggi Seongnam-si Bundang-gu Sampyeong-dong 629",
                "Gyeonggi Seongnam-si Bundang-gu Pangyoyeok-ro 166",
                "41135",
                "Gyeonggi-do",
                "Seongnam-si Bundang-gu",
                "Sampyeong-dong",
                new BigDecimal("37.3952280"),
                new BigDecimal("127.1109030"),
                LocalDateTime.of(2026, 7, 30, 8, 45),
                "CANCELED",
                "LOW",
                18,
                "WEAR",
                false,
                "LOW",
                new BigDecimal("0.7800")
        ));
    }

    private UserAccount ensureUser(
            String username,
            String password,
            String email,
            String name,
            UserRole role
    ) {
        return userAccountService.findByUsername(username)
                .orElseGet(() -> userAccountService.create(username, password, email, name, role));
    }

    private Long seedRobot(Long userId, String name, String serialNumber, String status) {
        jdbcTemplate.update("""
                INSERT INTO robots (user_id, name, serial_number, status, active)
                SELECT ?, ?, ?, ?, TRUE
                FROM DUAL
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM robots
                    WHERE serial_number = ?
                )
                """, userId, name, serialNumber, status, serialNumber);
        return jdbcTemplate.queryForObject(
                "SELECT id FROM robots WHERE serial_number = ?",
                Long.class,
                serialNumber
        );
    }

    private void seedDamage(DamageSeed seed) {
        jdbcTemplate.update("""
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
                    processing_priority,
                    created_at,
                    updated_at
                )
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                FROM DUAL
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM damages
                    WHERE description = ?
                      AND captured_at = ?
                )
                """,
                seed.robotId(),
                seed.reportedBy(),
                seed.assignedTo(),
                seed.description(),
                seed.addressName(),
                seed.roadAddressName(),
                seed.regionCode(),
                seed.region1DepthName(),
                seed.region2DepthName(),
                seed.region3DepthName(),
                seed.capturedAt().plusSeconds(2),
                seed.latitude(),
                seed.longitude(),
                seed.capturedAt(),
                seed.currentStatus(),
                seed.processingPriority(),
                seed.capturedAt().plusSeconds(5),
                seed.capturedAt().plusSeconds(5),
                seed.description(),
                seed.capturedAt()
        );

        Long damageId = jdbcTemplate.queryForObject(
                "SELECT id FROM damages WHERE description = ? AND captured_at = ? ORDER BY id ASC LIMIT 1",
                Long.class,
                seed.description(),
                seed.capturedAt()
        );
        seedDamageImage(damageId);
        seedDamageAiAnalysis(damageId, seed);
    }

    private void seedDamageImage(Long damageId) {
        jdbcTemplate.update("""
                INSERT INTO damage_images (
                    damage_id,
                    sort_order,
                    original_filename,
                    content_type,
                    size_bytes,
                    data
                )
                SELECT ?, 1, 'sample-damage.png', 'image/png', ?, ?
                FROM DUAL
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM damage_images
                    WHERE damage_id = ?
                      AND sort_order = 1
                )
                """, damageId, SAMPLE_PNG.length, SAMPLE_PNG, damageId);
    }

    private void seedDamageAiAnalysis(Long damageId, DamageSeed seed) {
        String rawResult = """
                {"damaged":%s,"damageScore":%d,"damageType":"%s","repairRequired":%s,"repairPriority":"%s","confidenceScore":%s}
                """.formatted(
                seed.damageScore() > 0,
                seed.damageScore(),
                seed.damageType(),
                seed.repairRequired(),
                seed.repairPriority(),
                seed.confidenceScore()
        ).trim();

        jdbcTemplate.update("""
                INSERT INTO damage_ai_analysis_results (
                    damage_id,
                    damaged,
                    damage_score,
                    damage_type,
                    repair_required,
                    repair_priority,
                    confidence_score,
                    analysis_status,
                    raw_result,
                    analyzed_at,
                    created_at
                )
                SELECT ?, ?, ?, ?, ?, ?, ?, 'SUCCESS', ?, ?, ?
                FROM DUAL
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM damage_ai_analysis_results
                    WHERE damage_id = ?
                      AND analysis_status = 'SUCCESS'
                )
                """,
                damageId,
                seed.damageScore() > 0,
                seed.damageScore(),
                seed.damageType(),
                seed.repairRequired(),
                seed.repairPriority(),
                seed.confidenceScore(),
                rawResult,
                seed.capturedAt().plusMinutes(2),
                seed.capturedAt().plusMinutes(2),
                damageId
        );
    }

    private record DamageSeed(
            Long robotId,
            Long reportedBy,
            Long assignedTo,
            String description,
            String addressName,
            String roadAddressName,
            String regionCode,
            String region1DepthName,
            String region2DepthName,
            String region3DepthName,
            BigDecimal latitude,
            BigDecimal longitude,
            LocalDateTime capturedAt,
            String currentStatus,
            String processingPriority,
            int damageScore,
            String damageType,
            boolean repairRequired,
            String repairPriority,
            BigDecimal confidenceScore
    ) {
    }
}
