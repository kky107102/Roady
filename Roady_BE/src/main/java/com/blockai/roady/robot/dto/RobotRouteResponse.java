package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.RobotRoute;
import com.blockai.roady.robot.domain.RobotRoutePoint;

import java.time.LocalDateTime;
import java.util.List;

public record RobotRouteResponse(
        Long id,
        Long robotId,
        Long createdBy,
        String name,
        String routeStatus,
        List<RobotRoutePointResponse> points,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {

    public static RobotRouteResponse from(RobotRoute route, List<RobotRoutePoint> points) {
        return new RobotRouteResponse(
                route.getId(),
                route.getRobotId(),
                route.getCreatedBy(),
                route.getName(),
                route.getRouteStatus().name(),
                points.stream().map(RobotRoutePointResponse::from).toList(),
                route.getCreatedAt(),
                route.getUpdatedAt()
        );
    }
}
