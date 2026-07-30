package com.blockai.roady.damage.domain;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class Damage {

    private Long id;
    private Long robotId;
    private Long reportedBy;
    private Long assignedTo;
    private String description;
    private String addressName;
    private String roadAddressName;
    private String regionCode;
    private String region1DepthName;
    private String region2DepthName;
    private String region3DepthName;
    private LocalDateTime geocodedAt;
    private BigDecimal latitude;
    private BigDecimal longitude;
    private LocalDateTime capturedAt;
    private String currentStatus;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Damage() {
    }

    public Damage(
            Long id,
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
            LocalDateTime geocodedAt,
            BigDecimal latitude,
            BigDecimal longitude,
            LocalDateTime capturedAt,
            String currentStatus,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {
        this.id = id;
        this.robotId = robotId;
        this.reportedBy = reportedBy;
        this.assignedTo = assignedTo;
        this.description = description;
        this.addressName = addressName;
        this.roadAddressName = roadAddressName;
        this.regionCode = regionCode;
        this.region1DepthName = region1DepthName;
        this.region2DepthName = region2DepthName;
        this.region3DepthName = region3DepthName;
        this.geocodedAt = geocodedAt;
        this.latitude = latitude;
        this.longitude = longitude;
        this.capturedAt = capturedAt;
        this.currentStatus = currentStatus;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getRobotId() {
        return robotId;
    }

    public void setRobotId(Long robotId) {
        this.robotId = robotId;
    }

    public Long getReportedBy() {
        return reportedBy;
    }

    public void setReportedBy(Long reportedBy) {
        this.reportedBy = reportedBy;
    }

    public Long getAssignedTo() {
        return assignedTo;
    }

    public void setAssignedTo(Long assignedTo) {
        this.assignedTo = assignedTo;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getAddressName() {
        return addressName;
    }

    public void setAddressName(String addressName) {
        this.addressName = addressName;
    }

    public String getRoadAddressName() {
        return roadAddressName;
    }

    public void setRoadAddressName(String roadAddressName) {
        this.roadAddressName = roadAddressName;
    }

    public String getRegionCode() {
        return regionCode;
    }

    public void setRegionCode(String regionCode) {
        this.regionCode = regionCode;
    }

    public String getRegion1DepthName() {
        return region1DepthName;
    }

    public void setRegion1DepthName(String region1DepthName) {
        this.region1DepthName = region1DepthName;
    }

    public String getRegion2DepthName() {
        return region2DepthName;
    }

    public void setRegion2DepthName(String region2DepthName) {
        this.region2DepthName = region2DepthName;
    }

    public String getRegion3DepthName() {
        return region3DepthName;
    }

    public void setRegion3DepthName(String region3DepthName) {
        this.region3DepthName = region3DepthName;
    }

    public LocalDateTime getGeocodedAt() {
        return geocodedAt;
    }

    public void setGeocodedAt(LocalDateTime geocodedAt) {
        this.geocodedAt = geocodedAt;
    }

    public BigDecimal getLatitude() {
        return latitude;
    }

    public void setLatitude(BigDecimal latitude) {
        this.latitude = latitude;
    }

    public BigDecimal getLongitude() {
        return longitude;
    }

    public void setLongitude(BigDecimal longitude) {
        this.longitude = longitude;
    }

    public LocalDateTime getCapturedAt() {
        return capturedAt;
    }

    public void setCapturedAt(LocalDateTime capturedAt) {
        this.capturedAt = capturedAt;
    }

    public String getCurrentStatus() {
        return currentStatus;
    }

    public void setCurrentStatus(String currentStatus) {
        this.currentStatus = currentStatus;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
