package com.blockai.roady.robot.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record CreateRobotRequest(
        @NotNull Long userId,
        @NotBlank @Size(max = 100) String name,
        @NotBlank @Size(max = 100) String serialNumber
) {
}
