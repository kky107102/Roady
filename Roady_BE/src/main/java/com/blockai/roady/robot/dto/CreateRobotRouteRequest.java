package com.blockai.roady.robot.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.util.List;

public record CreateRobotRouteRequest(
        @NotNull Long robotId,
        @NotBlank @Size(max = 100) String name,
        @NotEmpty @Size(min = 2, max = 200) List<@Valid RobotRoutePointRequest> points
) {
}
