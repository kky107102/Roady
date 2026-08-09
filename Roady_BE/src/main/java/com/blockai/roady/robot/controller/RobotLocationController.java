package com.blockai.roady.robot.controller;

import com.blockai.roady.robot.dto.RobotLocationState;
import com.blockai.roady.robot.service.RobotLocationService;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/robots")
public class RobotLocationController {

    private final RobotLocationService robotLocationService;

    public RobotLocationController(RobotLocationService robotLocationService) {
        this.robotLocationService = robotLocationService;
    }

    @GetMapping("/{robotId}/location/latest")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR', 'VIEWER')")
    public RobotLocationState getLatestRobotLocation(@PathVariable Long robotId) {
        return robotLocationService.findLatest(robotId)
                .orElseThrow(() -> new IllegalArgumentException("Robot location not found."));
    }
}
