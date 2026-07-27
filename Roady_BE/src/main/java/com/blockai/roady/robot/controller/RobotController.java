package com.blockai.roady.robot.controller;

import com.blockai.roady.robot.dto.CreateRobotRequest;
import com.blockai.roady.robot.dto.RobotResponse;
import com.blockai.roady.robot.dto.UpdateRobotActiveRequest;
import com.blockai.roady.robot.dto.UpdateRobotRequest;
import com.blockai.roady.robot.service.RobotService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/robots")
public class RobotController {

    private final RobotService robotService;

    public RobotController(RobotService robotService) {
        this.robotService = robotService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasRole('ADMIN')")
    public RobotResponse createRobot(@Valid @RequestBody CreateRobotRequest request) {
        return RobotResponse.from(robotService.create(
                request.userId(),
                request.name(),
                request.serialNumber()
        ));
    }

    @GetMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR', 'VIEWER')")
    public List<RobotResponse> getRobots() {
        return robotService.findAll().stream()
                .map(RobotResponse::from)
                .toList();
    }

    @GetMapping("/{robotId}")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR', 'VIEWER')")
    public RobotResponse getRobot(@PathVariable Long robotId) {
        return RobotResponse.from(robotService.get(robotId));
    }

    @PatchMapping("/{robotId}")
    @PreAuthorize("hasRole('ADMIN')")
    public RobotResponse updateRobot(
            @PathVariable Long robotId,
            @Valid @RequestBody UpdateRobotRequest request
    ) {
        return RobotResponse.from(robotService.update(
                robotId,
                request.userId(),
                request.name(),
                request.active()
        ));
    }

    @PatchMapping("/{robotId}/active")
    @PreAuthorize("hasRole('ADMIN')")
    public RobotResponse updateRobotActive(
            @PathVariable Long robotId,
            @Valid @RequestBody UpdateRobotActiveRequest request
    ) {
        return RobotResponse.from(robotService.updateActive(robotId, request.active()));
    }
}
