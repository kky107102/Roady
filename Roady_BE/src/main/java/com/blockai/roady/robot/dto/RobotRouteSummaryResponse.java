package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.RobotRoute;

import java.time.LocalDateTime;

public record RobotRouteSummaryResponse(
        Long id,
        Long robotId,
        Long createdBy,
        String name,
        String routeStatus,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {

    public static RobotRouteSummaryResponse from(RobotRoute route) {
        return new RobotRouteSummaryResponse(
                route.getId(),
                route.getRobotId(),
                route.getCreatedBy(),
                route.getName(),
                route.getRouteStatus().name(),
                route.getCreatedAt(),
                route.getUpdatedAt()
        );
    }
}
