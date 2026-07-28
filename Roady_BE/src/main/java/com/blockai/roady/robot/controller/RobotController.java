package com.blockai.roady.robot.controller;

import com.blockai.roady.robot.dto.CreateRobotRequest;
import com.blockai.roady.robot.dto.CreateRobotCommandRequest;
import com.blockai.roady.robot.dto.CreateRobotStatusLogRequest;
import com.blockai.roady.robot.dto.RobotCommandResponse;
import com.blockai.roady.robot.dto.RobotResponse;
import com.blockai.roady.robot.dto.RobotStatusLogResponse;
import com.blockai.roady.robot.dto.UpdateRobotCommandStatusRequest;
import com.blockai.roady.robot.dto.UpdateRobotActiveRequest;
import com.blockai.roady.robot.dto.UpdateRobotRequest;
import com.blockai.roady.robot.service.RobotCommandService;
import com.blockai.roady.robot.service.RobotService;
import com.blockai.roady.robot.service.RobotStatusLogService;
import com.blockai.roady.security.AuthenticatedUser;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
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
    private final RobotCommandService robotCommandService;
    private final RobotStatusLogService robotStatusLogService;

    public RobotController(
            RobotService robotService,
            RobotCommandService robotCommandService,
            RobotStatusLogService robotStatusLogService
    ) {
        this.robotService = robotService;
        this.robotCommandService = robotCommandService;
        this.robotStatusLogService = robotStatusLogService;
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
                .map(robot -> RobotResponse.from(
                        robot,
                        robotStatusLogService.findLatestByRobotIdIfExists(robot.getId()).orElse(null)
                ))
                .toList();
    }

    @GetMapping("/{robotId}")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR', 'VIEWER')")
    public RobotResponse getRobot(@PathVariable Long robotId) {
        var robot = robotService.get(robotId);
        return RobotResponse.from(
                robot,
                robotStatusLogService.findLatestByRobotIdIfExists(robotId).orElse(null)
        );
    }

    @PatchMapping("/{robotId}")
    @PreAuthorize("hasRole('ADMIN')")
    public RobotResponse updateRobot(
            @PathVariable Long robotId,
            @Valid @RequestBody UpdateRobotRequest request
    ) {
        var robot = robotService.update(
                robotId,
                request.userId(),
                request.name(),
                request.active()
        );
        return RobotResponse.from(
                robot,
                robotStatusLogService.findLatestByRobotIdIfExists(robotId).orElse(null)
        );
    }

    @PatchMapping("/{robotId}/active")
    @PreAuthorize("hasRole('ADMIN')")
    public RobotResponse updateRobotActive(
            @PathVariable Long robotId,
            @Valid @RequestBody UpdateRobotActiveRequest request
    ) {
        var robot = robotService.updateActive(robotId, request.active());
        return RobotResponse.from(
                robot,
                robotStatusLogService.findLatestByRobotIdIfExists(robotId).orElse(null)
        );
    }

    @PostMapping("/{robotId}/status-logs")
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public RobotStatusLogResponse createRobotStatusLog(
            @PathVariable Long robotId,
            @Valid @RequestBody CreateRobotStatusLogRequest request
    ) {
        return RobotStatusLogResponse.from(robotStatusLogService.create(
                robotId,
                request.latitude(),
                request.longitude(),
                request.batteryLevel(),
                request.operationStatus(),
                request.connectionStatus(),
                request.errorCode(),
                request.errorMessage(),
                request.recordedAt()
        ));
    }

    @GetMapping("/{robotId}/status-logs/latest")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR', 'VIEWER')")
    public RobotStatusLogResponse getLatestRobotStatusLog(@PathVariable Long robotId) {
        return RobotStatusLogResponse.from(robotStatusLogService.findLatestByRobotId(robotId)
                .orElseThrow(() -> new IllegalArgumentException("Robot status log not found.")));
    }

    @GetMapping("/{robotId}/status-logs")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public List<RobotStatusLogResponse> getRobotStatusLogs(@PathVariable Long robotId) {
        return robotStatusLogService.findByRobotId(robotId).stream()
                .map(RobotStatusLogResponse::from)
                .toList();
    }

    @PostMapping("/{robotId}/commands")
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public RobotCommandResponse createRobotCommand(
            @AuthenticationPrincipal AuthenticatedUser user,
            @PathVariable Long robotId,
            @Valid @RequestBody CreateRobotCommandRequest request
    ) {
        return RobotCommandResponse.from(robotCommandService.create(robotId, user.id(), request.commandType()));
    }

    @GetMapping("/{robotId}/commands")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public List<RobotCommandResponse> getRobotCommands(@PathVariable Long robotId) {
        return robotCommandService.findByRobotId(robotId).stream()
                .map(RobotCommandResponse::from)
                .toList();
    }

    @GetMapping("/{robotId}/commands/pending")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public List<RobotCommandResponse> getPendingRobotCommands(@PathVariable Long robotId) {
        return robotCommandService.findPendingByRobotId(robotId).stream()
                .map(RobotCommandResponse::from)
                .toList();
    }

    @PatchMapping("/{robotId}/commands/{commandId}/status")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public RobotCommandResponse updateRobotCommandStatus(
            @PathVariable Long robotId,
            @PathVariable Long commandId,
            @Valid @RequestBody UpdateRobotCommandStatusRequest request
    ) {
        return RobotCommandResponse.from(robotCommandService.updateStatus(
                robotId,
                commandId,
                request.commandStatus(),
                request.resultMessage()
        ));
    }
}
