package com.blockai.roady.robot.dto;

import jakarta.validation.constraints.Size;

public record UpdateRobotRequest(
        Long userId,
        @Size(max = 100) String name,
        Boolean active
) {
}
