package com.blockai.roady.robot.domain;

import java.time.LocalDateTime;

public class RobotRoute {

    private Long id;
    private Long robotId;
    private Long createdBy;
    private String name;
    private RobotRouteStatus routeStatus;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public RobotRoute() {
    }

    public RobotRoute(
            Long id,
            Long robotId,
            Long createdBy,
            String name,
            RobotRouteStatus routeStatus,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {
        this.id = id;
        this.robotId = robotId;
        this.createdBy = createdBy;
        this.name = name;
        this.routeStatus = routeStatus;
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

    public Long getCreatedBy() {
        return createdBy;
    }

    public void setCreatedBy(Long createdBy) {
        this.createdBy = createdBy;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public RobotRouteStatus getRouteStatus() {
        return routeStatus;
    }

    public void setRouteStatus(RobotRouteStatus routeStatus) {
        this.routeStatus = routeStatus;
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
