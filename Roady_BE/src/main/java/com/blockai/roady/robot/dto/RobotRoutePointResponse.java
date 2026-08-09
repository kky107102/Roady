package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.RobotRoutePoint;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record RobotRoutePointResponse(
        Long id,
        Long routeId,
        Integer pointOrder,
        BigDecimal latitude,
        BigDecimal longitude,
        String pointType,
        LocalDateTime createdAt
) {

    public static RobotRoutePointResponse from(RobotRoutePoint point) {
        return new RobotRoutePointResponse(
                point.getId(),
                point.getRouteId(),
                point.getPointOrder(),
                point.getLatitude(),
                point.getLongitude(),
                point.getPointType().name(),
                point.getCreatedAt()
        );
    }
}
