package com.blockai.roady.damage.service;

import com.blockai.roady.damage.domain.Damage;
import com.blockai.roady.damage.domain.DamageDashboardSummary;
import com.blockai.roady.damage.domain.DamageFilterCriteria;
import com.blockai.roady.damage.domain.DamageImage;
import com.blockai.roady.damage.domain.DamageImageMetadata;
import com.blockai.roady.damage.domain.DamageMapBounds;
import com.blockai.roady.damage.domain.DamageMapMarker;
import com.blockai.roady.damage.domain.DamageSearchCriteria;
import com.blockai.roady.damage.domain.DamageSearchItem;
import com.blockai.roady.damage.domain.DamageSearchPage;
import com.blockai.roady.damage.domain.DamageStatus;
import com.blockai.roady.damage.domain.DamageSummary;
import com.blockai.roady.damage.geocoding.GeocodedAddress;
import com.blockai.roady.damage.geocoding.KakaoReverseGeocodingClient;
import com.blockai.roady.damage.mapper.DamageMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Optional;

@Service
public class DamageService {

    private static final int MAX_IMAGE_COUNT = 50;
    private static final String DEFAULT_CONTENT_TYPE = "application/octet-stream";

    private final DamageMapper damageMapper;
    private final KakaoReverseGeocodingClient geocodingClient;

    public DamageService(DamageMapper damageMapper, KakaoReverseGeocodingClient geocodingClient) {
        this.damageMapper = damageMapper;
        this.geocodingClient = geocodingClient;
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
