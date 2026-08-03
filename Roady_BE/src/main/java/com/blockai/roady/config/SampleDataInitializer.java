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
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;

@Component
@Profile("!inmemory")
@ConditionalOnProperty(prefix = "roady.sample-data", name = "enabled", havingValue = "true", matchIfMissing = true)
public class SampleDataInitializer implements ApplicationRunner {

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
                "roady0810",
                "inspector@roady.local",
                "점검 담당자",
                UserRole.INSPECTOR
        );
        UserAccount repairer = ensureUser(
                "repairer",
                "roady0810",
                "repairer@roady.local",
                "보수 담당자",
                UserRole.REPAIRER
        );

        Long roadyOneId = seedRobot(inspector.id(), "로디 1호", "RD-202608030001", "MOVING");
        Long roadyTwoId = seedRobot(inspector.id(), "로디 2호", "RD-202608030002", "INSPECTING");
        Long roadyThreeId = seedRobot(inspector.id(), "로디 3호", "RD-202608030003", "STANDBY");
        Long roadyFourId = seedRobot(inspector.id(), "로디 4호", "RD-202608030004", "CHARGING");
        Long roadyFiveId = seedRobot(inspector.id(), "로디 5호", "RD-202608030005", "STOPPED");
        Long roadySixId = seedRobot(inspector.id(), "로디 6호", "RD-202608030006", "ERROR");
        Long roadySevenId = seedRobot(inspector.id(), "로디 7호", "RD-202608030007", "MOVING");
        Long roadyEightId = seedRobot(inspector.id(), "로디 8호", "RD-202608030008", "STANDBY");

        seedRobotStatusLog(roadyOneId, "37.5012748", "127.0396250", 92, "MOVING", "CONNECTED", null, null);
        seedRobotStatusLog(roadyTwoId, "37.4979520", "127.0276190", 86, "INSPECTING", "CONNECTED", null, null);
        seedRobotStatusLog(roadyThreeId, "37.5088440", "127.0631600", 74, "STANDBY", "CONNECTED", null, null);
        seedRobotStatusLog(roadyFourId, "37.5142500", "127.0572200", 51, "CHARGING", "CONNECTED", null, null);
        seedRobotStatusLog(roadyFiveId, "37.5228900", "127.0370100", 68, "STOPPED", "CONNECTED", null, null);
        seedRobotStatusLog(roadySixId, "37.4865460", "127.0450210", 23, "ERROR", "CONNECTED", "E_SENSOR", "점자블록 탐지 센서 점검 필요");
        seedRobotStatusLog(roadySevenId, "37.5271300", "127.0285100", 59, "MOVING", "DISCONNECTED", null, null);
        seedRobotStatusLog(roadyEightId, "37.5238500", "127.0566700", 96, "STANDBY", "DISCONNECTED", null, null);

        seedDamage(new DamageSeed(
                roadyOneId,
                inspector.id(),
                repairer.id(),
                "테헤란로 보도 점자블록 파손 탐지",
                "서울특별시 강남구 역삼동 737",
                "서울특별시 강남구 테헤란로 212",
                "11680",
                "서울특별시",
                "강남구",
                "역삼동",
                new BigDecimal("37.5012748"),
                new BigDecimal("127.0396250"),
                LocalDateTime.of(2026, 8, 3, 9, 10),
                "COLLECTED",
                "NORMAL",
                61,
                "BREAKAGE",
                true,
                "NORMAL",
                new BigDecimal("0.8600"),
                "braille-block-yeoksam-collected.svg",
                "점자블록 파손",
                "#f59e0b"
        ));
        seedDamage(new DamageSeed(
                roadyTwoId,
                inspector.id(),
                repairer.id(),
                "강남역 11번 출구 점자블록 들뜸 탐지",
                "서울특별시 강남구 역삼동 858",
                "서울특별시 강남구 강남대로 396",
                "11680",
                "서울특별시",
                "강남구",
                "역삼동",
                new BigDecimal("37.4979520"),
                new BigDecimal("127.0276190"),
                LocalDateTime.of(2026, 8, 3, 9, 25),
                "AI_ANALYZING",
                "HIGH",
                78,
                "BREAKAGE",
                true,
                "HIGH",
                new BigDecimal("0.9000"),
                "braille-block-gangnam-ai-analyzing.svg",
                "들뜸",
                "#ef4444"
        ));
        seedDamage(new DamageSeed(
                roadyThreeId,
                inspector.id(),
                repairer.id(),
                "삼성역 횡단보도 점자블록 균열 탐지",
                "서울특별시 강남구 삼성동 159",
                "서울특별시 강남구 테헤란로 517",
                "11680",
                "서울특별시",
                "강남구",
                "삼성동",
                new BigDecimal("37.5088440"),
                new BigDecimal("127.0631600"),
                LocalDateTime.of(2026, 8, 3, 10, 5),
                "AI_ANALYZED",
                "HIGH",
                84,
                "CRACK",
                true,
                "HIGH",
                new BigDecimal("0.9300"),
                "braille-block-samseong-crack.svg",
                "균열",
                "#dc2626"
        ));
        seedDamage(new DamageSeed(
                roadyFourId,
                inspector.id(),
                repairer.id(),
                "봉은사역 보도 점자블록 이탈 탐지",
                "서울특별시 강남구 삼성동 73",
                "서울특별시 강남구 봉은사로 524",
                "11680",
                "서울특별시",
                "강남구",
                "삼성동",
                new BigDecimal("37.5142500"),
                new BigDecimal("127.0572200"),
                LocalDateTime.of(2026, 8, 3, 10, 30),
                "REQUESTED",
                "URGENT",
                92,
                "BREAKAGE",
                true,
                "URGENT",
                new BigDecimal("0.9600"),
                "braille-block-bongeunsa-detached.svg",
                "이탈",
                "#b91c1c"
        ));
        seedDamage(new DamageSeed(
                roadyFiveId,
                inspector.id(),
                repairer.id(),
                "도산대로 버스정류장 점자블록 마모 탐지",
                "서울특별시 강남구 신사동 664",
                "서울특별시 강남구 도산대로 318",
                "11680",
                "서울특별시",
                "강남구",
                "신사동",
                new BigDecimal("37.5228900"),
                new BigDecimal("127.0370100"),
                LocalDateTime.of(2026, 8, 3, 11, 0),
                "REPAIR_SCHEDULED",
                "NORMAL",
                56,
                "WEAR",
                true,
                "NORMAL",
                new BigDecimal("0.8200"),
                "braille-block-dosan-wear.svg",
                "마모",
                "#eab308"
        ));
        seedDamage(new DamageSeed(
                roadySixId,
                inspector.id(),
                repairer.id(),
                "개포로 보행로 점자블록 침하 탐지",
                "서울특별시 강남구 개포동 186",
                "서울특별시 강남구 개포로 303",
                "11680",
                "서울특별시",
                "강남구",
                "개포동",
                new BigDecimal("37.4865460"),
                new BigDecimal("127.0450210"),
                LocalDateTime.of(2026, 8, 3, 11, 20),
                "REPAIR_IN_PROGRESS",
                "URGENT",
                89,
                "BREAKAGE",
                true,
                "URGENT",
                new BigDecimal("0.9400"),
                "braille-block-gaepo-subsidence.svg",
                "침하",
                "#7c2d12"
        ));
        seedDamage(new DamageSeed(
                roadySevenId,
                inspector.id(),
                repairer.id(),
                "압구정로 횡단보도 점자블록 균열 보수 완료",
                "서울특별시 강남구 압구정동 429",
                "서울특별시 강남구 압구정로 165",
                "11680",
                "서울특별시",
                "강남구",
                "압구정동",
                new BigDecimal("37.5271300"),
                new BigDecimal("127.0285100"),
                LocalDateTime.of(2026, 8, 3, 13, 15),
                "REPAIR_COMPLETED",
                "LOW",
                42,
                "CRACK",
                true,
                "LOW",
                new BigDecimal("0.7800"),
                "braille-block-apgujeong-completed.svg",
                "보수 완료",
                "#22c55e"
        ));
        seedDamage(new DamageSeed(
                roadyEightId,
                inspector.id(),
                null,
                "청담동 보도 점자블록 오탐 신고 취소",
                "서울특별시 강남구 청담동 133",
                "서울특별시 강남구 영동대로 513",
                "11680",
                "서울특별시",
                "강남구",
                "청담동",
                new BigDecimal("37.5238500"),
                new BigDecimal("127.0566700"),
                LocalDateTime.of(2026, 8, 3, 14, 5),
                "CANCELED",
                "LOW",
                19,
                "WEAR",
                false,
                "LOW",
                new BigDecimal("0.6100"),
                "braille-block-cheongdam-canceled.svg",
                "취소",
                "#64748b"
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

    private void seedRobotStatusLog(
            Long robotId,
            String latitude,
            String longitude,
            int batteryLevel,
            String operationStatus,
            String connectionStatus,
            String errorCode,
            String errorMessage
    ) {
        jdbcTemplate.update("""
                INSERT INTO robot_status_logs (
                    robot_id,
                    latitude,
                    longitude,
                    battery_level,
                    operation_status,
                    connection_status,
                    error_code,
                    error_message,
                    recorded_at
                )
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?
                FROM DUAL
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM robot_status_logs
                    WHERE robot_id = ?
                )
                """,
                robotId,
                new BigDecimal(latitude),
                new BigDecimal(longitude),
                batteryLevel,
                operationStatus,
                connectionStatus,
                errorCode,
                errorMessage,
                LocalDateTime.of(2026, 8, 3, 9, 0),
                robotId
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
        seedDamageImage(damageId, seed);
        seedDamageAiAnalysis(damageId, seed);
    }

    private void seedDamageImage(Long damageId, DamageSeed seed) {
        byte[] imageData = sampleSvg(seed).getBytes(StandardCharsets.UTF_8);
        jdbcTemplate.update("""
                INSERT INTO damage_images (
                    damage_id,
                    sort_order,
                    original_filename,
                    content_type,
                    size_bytes,
                    data
                )
                SELECT ?, 1, ?, 'image/svg+xml', ?, ?
                FROM DUAL
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM damage_images
                    WHERE damage_id = ?
                      AND sort_order = 1
                )
                """, damageId, seed.imageFilename(), imageData.length, imageData, damageId);
    }

    private String sampleSvg(DamageSeed seed) {
        String label = xml(seed.imageLabel());
        String description = xml(seed.description());
        String roadAddressName = xml(seed.roadAddressName());
        String accentColor = xml(seed.imageAccentColor());
        return """
                <svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
                  <rect width="640" height="360" fill="#f3f4f6"/>
                  <rect x="0" y="210" width="640" height="150" fill="#475569"/>
                  <rect x="40" y="192" width="560" height="88" rx="10" fill="#facc15"/>
                  <g fill="#a16207">
                    <circle cx="82" cy="220" r="9"/><circle cx="122" cy="220" r="9"/><circle cx="162" cy="220" r="9"/><circle cx="202" cy="220" r="9"/><circle cx="242" cy="220" r="9"/><circle cx="282" cy="220" r="9"/><circle cx="322" cy="220" r="9"/><circle cx="362" cy="220" r="9"/><circle cx="402" cy="220" r="9"/><circle cx="442" cy="220" r="9"/><circle cx="482" cy="220" r="9"/><circle cx="522" cy="220" r="9"/>
                    <circle cx="82" cy="252" r="9"/><circle cx="122" cy="252" r="9"/><circle cx="162" cy="252" r="9"/><circle cx="202" cy="252" r="9"/><circle cx="242" cy="252" r="9"/><circle cx="282" cy="252" r="9"/><circle cx="322" cy="252" r="9"/><circle cx="362" cy="252" r="9"/><circle cx="402" cy="252" r="9"/><circle cx="442" cy="252" r="9"/><circle cx="482" cy="252" r="9"/><circle cx="522" cy="252" r="9"/>
                  </g>
                  <path d="M178 196l34 28-22 25 46 31M352 193l-20 35 42 22-18 31" fill="none" stroke="%s" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
                  <rect x="40" y="36" width="560" height="118" rx="18" fill="#ffffff"/>
                  <text x="64" y="82" font-family="Arial, sans-serif" font-size="32" font-weight="700" fill="#111827">%s</text>
                  <text x="64" y="120" font-family="Arial, sans-serif" font-size="21" fill="#475569">%s</text>
                  <rect x="454" y="50" width="120" height="42" rx="21" fill="%s"/>
                  <text x="514" y="78" text-anchor="middle" font-family="Arial, sans-serif" font-size="21" font-weight="700" fill="#ffffff">%s</text>
                </svg>
                """.formatted(
                accentColor,
                description,
                roadAddressName,
                accentColor,
                label
        ).trim();
    }

    private String xml(String text) {
        return text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;");
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
            BigDecimal confidenceScore,
            String imageFilename,
            String imageLabel,
            String imageAccentColor
    ) {
    }
}
