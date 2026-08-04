package com.blockai.roady.damage.service;

import com.blockai.roady.damage.domain.Damage;
import com.blockai.roady.damage.domain.DamageDashboardSummary;
import com.blockai.roady.damage.domain.DamageFilterCriteria;
import com.blockai.roady.damage.domain.DamageImage;
import com.blockai.roady.damage.domain.DamageImageMetadata;
import com.blockai.roady.damage.domain.DamageMapBounds;
import com.blockai.roady.damage.domain.DamageMapMarker;
import com.blockai.roady.damage.domain.DamageProcessingPriority;
import com.blockai.roady.damage.domain.DamageSearchCriteria;
import com.blockai.roady.damage.domain.DamageSearchItem;
import com.blockai.roady.damage.domain.DamageSearchPage;
import com.blockai.roady.damage.domain.DamageStatus;
import com.blockai.roady.damage.domain.DamageSummary;
import com.blockai.roady.damage.domain.ReviewDamageType;
import com.blockai.roady.damage.geocoding.GeocodedAddress;
import com.blockai.roady.damage.geocoding.KakaoReverseGeocodingClient;
import com.blockai.roady.damage.mapper.DamageMapper;
import com.blockai.roady.user.domain.UserRole;
import com.blockai.roady.user.service.UserAccountService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;

@Service
public class DamageService {

    private static final int MAX_IMAGE_COUNT = 50;
    private static final int MAX_REVIEW_NOTE_LENGTH = 1000;
    private static final int MAX_REPAIR_REQUEST_NOTE_LENGTH = 1000;
    private static final String DEFAULT_CONTENT_TYPE = "application/octet-stream";
    private static final Set<String> REVIEW_STATUSES = Set.of(
            "AI_ANALYZED",
            "REQUESTED",
            "CANCELED"
    );

    private final DamageMapper damageMapper;
    private final KakaoReverseGeocodingClient geocodingClient;
    private final UserAccountService userAccountService;

    public DamageService(
            DamageMapper damageMapper,
            KakaoReverseGeocodingClient geocodingClient,
            UserAccountService userAccountService
    ) {
        this.damageMapper = damageMapper;
        this.geocodingClient = geocodingClient;
        this.userAccountService = userAccountService;
    }

    @Transactional
    public DamageSummary create(
            Long robotId,
            Long reportedBy,
            Long assignedTo,
            String description,
            BigDecimal latitude,
            BigDecimal longitude,
            LocalDateTime capturedAt,
            List<MultipartFile> images
    ) {
        validateImages(images);

        Damage damage = new Damage();
        damage.setRobotId(robotId);
        damage.setReportedBy(reportedBy);
        damage.setAssignedTo(assignedTo);
        damage.setDescription(description);
        damage.setLatitude(latitude);
        damage.setLongitude(longitude);
        damage.setCapturedAt(capturedAt);
        damage.setCurrentStatus("COLLECTED");
        applyReverseGeocoding(damage);
        damageMapper.insertDamage(damage);

        for (int index = 0; index < images.size(); index++) {
            damageMapper.insertImage(toDamageImage(damage.getId(), index, images.get(index)));
        }

        return getSummary(damage.getId());
    }

    @Transactional(readOnly = true)
    public DamageSearchPage search(DamageSearchCriteria criteria) {
        List<DamageSearchItem> content = damageMapper.searchSummaries(
                criteria.from(),
                criteria.to(),
                criteria.status(),
                criteria.robotId(),
                criteria.assignedTo(),
                criteria.regionCode(),
                criteria.caseNumber(),
                criteria.addressKeyword(),
                criteria.offset(),
                criteria.size()
        );
        long totalElements = damageMapper.countSummaries(
                criteria.from(),
                criteria.to(),
                criteria.status(),
                criteria.robotId(),
                criteria.assignedTo(),
                criteria.regionCode(),
                criteria.caseNumber(),
                criteria.addressKeyword()
        );
        return DamageSearchPage.of(content, criteria, totalElements);
    }

    @Transactional(readOnly = true)
    public DamageDashboardSummary summarize(DamageFilterCriteria criteria) {
        var statusCounts = new LinkedHashMap<String, Long>();
        for (DamageStatus status : DamageStatus.values()) {
            statusCounts.put(status.name(), 0L);
        }

        long total = 0;
        long unassigned = 0;
        var groupedCounts = damageMapper.summarizeByStatus(
                criteria.from(),
                criteria.to(),
                criteria.status(),
                criteria.robotId(),
                criteria.assignedTo(),
                criteria.regionCode()
        );
        for (var groupedCount : groupedCounts) {
            statusCounts.put(groupedCount.status(), groupedCount.total());
            total += groupedCount.total();
            unassigned += groupedCount.unassigned();
        }

        return new DamageDashboardSummary(total, unassigned, statusCounts);
    }

    @Transactional(readOnly = true)
    public List<DamageMapMarker> findMapMarkers(DamageFilterCriteria criteria, DamageMapBounds bounds) {
        return damageMapper.findMapMarkers(
                criteria.from(),
                criteria.to(),
                criteria.status(),
                criteria.robotId(),
                criteria.assignedTo(),
                criteria.regionCode(),
                bounds.south(),
                bounds.north(),
                bounds.west(),
                bounds.east()
        );
    }

    @Transactional(readOnly = true)
    public DamageSummary getSummary(Long damageId) {
        return Optional.ofNullable(damageMapper.findSummaryById(damageId))
                .orElseThrow(() -> new IllegalArgumentException("Damage not found."));
    }

    @Transactional
    public DamageSummary updateReview(
            Long damageId,
            String status,
            String processingPriority,
            String reviewDamageType,
            String reviewNote
    ) {
        String normalizedStatus = normalizeReviewStatus(status);
        String normalizedPriority = null;
        String normalizedReviewDamageType = null;
        String normalizedReviewNote = null;

        if ("REQUESTED".equals(normalizedStatus)) {
            normalizedPriority = normalizeRequiredProcessingPriority(processingPriority);
            normalizedReviewDamageType = normalizeRequiredReviewDamageType(reviewDamageType);
            normalizedReviewNote = normalizeReviewNote(reviewNote);
        }

        getSummary(damageId);
        damageMapper.updateReview(
                damageId,
                normalizedStatus,
                normalizedPriority,
                normalizedReviewDamageType,
                normalizedReviewNote
        );
        return getSummary(damageId);
    }

    @Transactional
    public DamageSummary requestRepair(
            Long damageId,
            Long requestedBy,
            String processingPriority,
            String reviewDamageType,
            Long repairerId,
            String note
    ) {
        if (requestedBy == null) {
            throw new IllegalArgumentException("Authenticated user is required.");
        }

        String normalizedNote = normalizeRepairRequestNote(note);
        Long normalizedRepairerId = normalizeRepairerId(repairerId);
        DamageSummary damage = getSummary(damageId);
        if (!"REQUESTED".equals(damage.currentStatus())) {
            throw new IllegalArgumentException("Only REQUESTED damage can move to repair in progress.");
        }

        String normalizedPriority = normalizeRepairProcessingPriority(processingPriority, damage.processingPriority());
        String normalizedReviewDamageType = normalizeRepairReviewDamageType(reviewDamageType, damage.reviewDamageType());
        int updatedRows = damageMapper.transitionToRepairInProgress(
                damageId,
                normalizedPriority,
                normalizedReviewDamageType,
                normalizedRepairerId
        );
        if (updatedRows != 1) {
            throw new IllegalArgumentException("Damage is no longer in REQUESTED status.");
        }

        damageMapper.insertRepairRequestHistory(
                damageId,
                requestedBy,
                normalizedRepairerId,
                "REQUESTED",
                "REPAIR_IN_PROGRESS",
                normalizedNote,
                LocalDateTime.now()
        );
        return getSummary(damageId);
    }

    @Transactional
    public DamageSummary updateRepairRequest(
            Long damageId,
            Long requestedBy,
            String processingPriority,
            String reviewDamageType,
            Long repairerId,
            String note
    ) {
        if (requestedBy == null) {
            throw new IllegalArgumentException("Authenticated user is required.");
        }

        String normalizedNote = normalizeRepairRequestNote(note);
        String normalizedPriority = normalizeProcessingPriority(processingPriority);
        String normalizedReviewDamageType = normalizeReviewDamageType(reviewDamageType);
        Long normalizedRepairerId = normalizeRepairerId(repairerId);
        DamageSummary damage = getSummary(damageId);
        if (!"REPAIR_IN_PROGRESS".equals(damage.currentStatus())) {
            throw new IllegalArgumentException("Only REPAIR_IN_PROGRESS damage can update repair request.");
        }

        int updatedRows = damageMapper.updateRepairRequest(
                damageId,
                normalizedPriority,
                normalizedReviewDamageType,
                normalizedRepairerId
        );
        if (updatedRows != 1) {
            throw new IllegalArgumentException("Damage is no longer in REPAIR_IN_PROGRESS status.");
        }

        damageMapper.insertRepairRequestHistory(
                damageId,
                requestedBy,
                normalizedRepairerId,
                "REPAIR_IN_PROGRESS",
                "REPAIR_IN_PROGRESS",
                normalizedNote,
                LocalDateTime.now()
        );
        return getSummary(damageId);
    }

    @Transactional
    public DamageSummary completeRepair(Long damageId, Long requestedBy, LocalDate completedAt, String note) {
        if (requestedBy == null) {
            throw new IllegalArgumentException("Authenticated user is required.");
        }

        LocalDate normalizedCompletedAt = normalizeRepairCompletedAt(completedAt);
        String normalizedNote = normalizeRepairRequestNote(note);
        DamageSummary damage = getSummary(damageId);
        if (!"REPAIR_IN_PROGRESS".equals(damage.currentStatus())) {
            throw new IllegalArgumentException("Only REPAIR_IN_PROGRESS damage can move to REPAIR_COMPLETED.");
        }

        int updatedRows = damageMapper.completeRepair(damageId, normalizedCompletedAt, normalizedNote);
        if (updatedRows != 1) {
            throw new IllegalArgumentException("Damage is no longer in REPAIR_IN_PROGRESS status.");
        }

        damageMapper.insertRepairRequestHistory(
                damageId,
                requestedBy,
                damage.repairerId(),
                "REPAIR_IN_PROGRESS",
                "REPAIR_COMPLETED",
                normalizedNote,
                LocalDateTime.now()
        );
        return getSummary(damageId);
    }

    @Transactional
    public DamageSummary cancelRepair(Long damageId, Long requestedBy, String note) {
        if (requestedBy == null) {
            throw new IllegalArgumentException("Authenticated user is required.");
        }

        String normalizedNote = normalizeRepairRequestNote(note);
        DamageSummary damage = getSummary(damageId);
        if (!"REPAIR_IN_PROGRESS".equals(damage.currentStatus())) {
            throw new IllegalArgumentException("Only REPAIR_IN_PROGRESS damage can move to REQUESTED.");
        }

        int updatedRows = damageMapper.cancelRepairRequest(damageId);
        if (updatedRows != 1) {
            throw new IllegalArgumentException("Damage is no longer in REPAIR_IN_PROGRESS status.");
        }

        damageMapper.insertRepairRequestHistory(
                damageId,
                requestedBy,
                damage.repairerId(),
                "REPAIR_IN_PROGRESS",
                "REQUESTED",
                normalizedNote,
                LocalDateTime.now()
        );
        return getSummary(damageId);
    }

    @Transactional(readOnly = true)
    public List<DamageImageMetadata> getImageMetadata(Long damageId) {
        getSummary(damageId);
        return damageMapper.findImageMetadataByDamageId(damageId);
    }

    @Transactional(readOnly = true)
    public DamageImage getImage(Long damageId, Long imageId) {
        getSummary(damageId);
        return Optional.ofNullable(damageMapper.findImageById(damageId, imageId))
                .orElseThrow(() -> new IllegalArgumentException("Damage image not found."));
    }

    private void applyReverseGeocoding(Damage damage) {
        geocodingClient.reverseGeocode(damage.getLatitude(), damage.getLongitude())
                .ifPresent(geocodedAddress -> applyGeocodedAddress(damage, geocodedAddress));
    }

    private void applyGeocodedAddress(Damage damage, GeocodedAddress geocodedAddress) {
        damage.setAddressName(geocodedAddress.addressName());
        damage.setRoadAddressName(geocodedAddress.roadAddressName());
        damage.setRegionCode(geocodedAddress.regionCode());
        damage.setRegion1DepthName(geocodedAddress.region1DepthName());
        damage.setRegion2DepthName(geocodedAddress.region2DepthName());
        damage.setRegion3DepthName(geocodedAddress.region3DepthName());
        damage.setGeocodedAt(geocodedAddress.geocodedAt());
    }

    private DamageImage toDamageImage(Long damageId, int index, MultipartFile file) {
        DamageImage image = new DamageImage();
        image.setDamageId(damageId);
        image.setSortOrder(index + 1);
        image.setOriginalFilename(cleanFilename(file.getOriginalFilename(), index));
        image.setContentType(contentType(file));
        image.setSizeBytes(file.getSize());
        image.setData(readBytes(file));
        return image;
    }

    private void validateImages(List<MultipartFile> images) {
        if (images == null || images.isEmpty()) {
            throw new IllegalArgumentException("At least one image is required.");
        }
        if (images.size() > MAX_IMAGE_COUNT) {
            throw new IllegalArgumentException("Up to 50 images can be uploaded per damage.");
        }

        for (MultipartFile image : images) {
            if (image == null || image.isEmpty()) {
                throw new IllegalArgumentException("Empty image files cannot be uploaded.");
            }

            String contentType = contentType(image).toLowerCase(Locale.ROOT);
            if (!contentType.startsWith("image/")) {
                throw new IllegalArgumentException("Only image files can be uploaded.");
            }
        }
    }

    private String normalizeReviewStatus(String status) {
        if (!StringUtils.hasText(status)) {
            throw new IllegalArgumentException("Damage review status is required.");
        }
        String normalized = status.trim().toUpperCase(Locale.ROOT);
        if (!DamageStatus.contains(normalized) || !REVIEW_STATUSES.contains(normalized)) {
            throw new IllegalArgumentException("Invalid damage review status.");
        }
        return normalized;
    }

    private String normalizeRequiredProcessingPriority(String processingPriority) {
        String normalized = normalizeProcessingPriority(processingPriority);
        if (normalized == null) {
            throw new IllegalArgumentException("processingPriority is required when status is REQUESTED.");
        }
        return normalized;
    }

    private String normalizeRequiredReviewDamageType(String reviewDamageType) {
        if (!StringUtils.hasText(reviewDamageType)) {
            throw new IllegalArgumentException("reviewDamageType is required when status is REQUESTED.");
        }
        String normalized = reviewDamageType.trim().toUpperCase(Locale.ROOT);
        if (!ReviewDamageType.contains(normalized)) {
            throw new IllegalArgumentException("Invalid review damage type.");
        }
        return normalized;
    }

    private String normalizeReviewNote(String reviewNote) {
        if (!StringUtils.hasText(reviewNote)) {
            return null;
        }
        String normalized = reviewNote.trim();
        if (normalized.length() > MAX_REVIEW_NOTE_LENGTH) {
            throw new IllegalArgumentException("reviewNote must be 1000 characters or less.");
        }
        return normalized;
    }

    private String normalizeRepairRequestNote(String note) {
        if (!StringUtils.hasText(note)) {
            return null;
        }
        String normalized = note.trim();
        if (normalized.length() > MAX_REPAIR_REQUEST_NOTE_LENGTH) {
            throw new IllegalArgumentException("note must be 1000 characters or less.");
        }
        return normalized;
    }

    private LocalDate normalizeRepairCompletedAt(LocalDate completedAt) {
        if (completedAt == null) {
            throw new IllegalArgumentException("completedAt is required.");
        }
        if (completedAt.isAfter(LocalDate.now())) {
            throw new IllegalArgumentException("completedAt cannot be a future date.");
        }
        return completedAt;
    }

    private String normalizeRepairProcessingPriority(String processingPriority, String fallback) {
        String normalized = normalizeProcessingPriority(processingPriority);
        return normalized == null ? fallback : normalized;
    }

    private String normalizeRepairReviewDamageType(String reviewDamageType, String fallback) {
        String normalized = normalizeReviewDamageType(reviewDamageType);
        return normalized == null ? fallback : normalized;
    }

    private String normalizeReviewDamageType(String reviewDamageType) {
        if (!StringUtils.hasText(reviewDamageType)) {
            return null;
        }
        String normalized = reviewDamageType.trim().toUpperCase(Locale.ROOT);
        if (!ReviewDamageType.contains(normalized)) {
            throw new IllegalArgumentException("Invalid review damage type.");
        }
        return normalized;
    }

    private Long normalizeRepairerId(Long repairerId) {
        if (repairerId == null) {
            return null;
        }
        var repairer = userAccountService.findById(repairerId)
                .orElseThrow(() -> new IllegalArgumentException("Repairer not found."));
        if (repairer.role() != UserRole.REPAIRER) {
            throw new IllegalArgumentException("repairerId must reference a REPAIRER user.");
        }
        return repairer.id();
    }

    private String normalizeProcessingPriority(String processingPriority) {
        if (!StringUtils.hasText(processingPriority)) {
            return null;
        }
        String normalized = processingPriority.trim().toUpperCase(Locale.ROOT);
        if (!DamageProcessingPriority.contains(normalized)) {
            throw new IllegalArgumentException("Invalid damage processing priority.");
        }
        return normalized;
    }

    private String cleanFilename(String originalFilename, int index) {
        String filename = StringUtils.cleanPath(Optional.ofNullable(originalFilename).orElse("image-" + (index + 1)));
        if (!StringUtils.hasText(filename)) {
            return "image-" + (index + 1);
        }
        return filename;
    }

    private String contentType(MultipartFile file) {
        String contentType = file.getContentType();
        if (!StringUtils.hasText(contentType)) {
            return DEFAULT_CONTENT_TYPE;
        }
        return contentType;
    }

    private byte[] readBytes(MultipartFile file) {
        try {
            return file.getBytes();
        } catch (IOException ex) {
            throw new IllegalArgumentException("Failed to read uploaded image.", ex);
        }
    }
}
