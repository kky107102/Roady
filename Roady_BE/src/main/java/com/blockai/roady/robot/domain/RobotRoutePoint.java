package com.blockai.roady.robot.domain;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class RobotRoutePoint {

    private Long id;
    private Long routeId;
    private Integer pointOrder;
    private BigDecimal latitude;
    private BigDecimal longitude;
    private RobotRoutePointType pointType;
    private LocalDateTime createdAt;

    public RobotRoutePoint() {
    }

    public RobotRoutePoint(
            Long id,
            Long routeId,
            Integer pointOrder,
            BigDecimal latitude,
            BigDecimal longitude,
            RobotRoutePointType pointType,
            LocalDateTime createdAt
    ) {
        this.id = id;
        this.routeId = routeId;
        this.pointOrder = pointOrder;
        this.latitude = latitude;
        this.longitude = longitude;
        this.pointType = pointType;
        this.createdAt = createdAt;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getRouteId() {
        return routeId;
    }

    public void setRouteId(Long routeId) {
        this.routeId = routeId;
    }

    public Integer getPointOrder() {
        return pointOrder;
    }

    public void setPointOrder(Integer pointOrder) {
        this.pointOrder = pointOrder;
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

    public RobotRoutePointType getPointType() {
        return pointType;
    }

    public void setPointType(RobotRoutePointType pointType) {
        this.pointType = pointType;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
