package com.blockai.roady.robot.dto;

import jakarta.validation.constraints.NotNull;

public record UpdateRobotActiveRequest(
        @NotNull Boolean active
) {
}
