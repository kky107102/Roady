package com.blockai.roady.robot.dto;

import com.blockai.roady.robot.domain.RobotRouteStatus;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;

import java.util.List;

public record UpdateRobotRouteRequest(
        @NotBlank @Size(max = 100) String name,
        RobotRouteStatus routeStatus,
        @NotEmpty @Size(min = 2, max = 200) List<@Valid RobotRoutePointRequest> points
) {
}
