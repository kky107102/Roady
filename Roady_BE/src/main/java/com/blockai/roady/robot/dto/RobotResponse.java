package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.Robot;

import java.time.LocalDateTime;

public record RobotResponse(
        Long id,
        Long userId,
        String name,
        String serialNumber,
        String status,
        boolean active,
        RobotLatestStatusResponse latestStatus,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {

    public static RobotResponse from(Robot robot) {
        return new RobotResponse(
                robot.getId(),
                robot.getUserId(),
                robot.getName(),
                robot.getSerialNumber(),
                robot.getStatus().name(),
                robot.isActive(),
                null,
                robot.getCreatedAt(),
                robot.getUpdatedAt()
        );
    }
}
