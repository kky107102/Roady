package com.blockai.roady.robot.controller;

import com.blockai.roady.robot.domain.RobotRouteStatus;
import com.blockai.roady.robot.dto.CreateRobotRouteRequest;
import com.blockai.roady.robot.dto.RobotRouteResponse;
import com.blockai.roady.robot.dto.RobotRouteSummaryResponse;
import com.blockai.roady.robot.dto.UpdateRobotRouteRequest;
import com.blockai.roady.robot.service.RobotRouteService;
import com.blockai.roady.security.AuthenticatedUser;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/robot-routes")
public class RobotRouteController {

    private final RobotRouteService robotRouteService;

    public RobotRouteController(RobotRouteService robotRouteService) {
        this.robotRouteService = robotRouteService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public RobotRouteResponse createRobotRoute(
            @AuthenticationPrincipal AuthenticatedUser user,
            @Valid @RequestBody CreateRobotRouteRequest request
    ) {
        var route = robotRouteService.create(
                request.robotId(),
                user.id(),
                request.name(),
                request.points()
        );
        return RobotRouteResponse.from(route, robotRouteService.getPoints(route.getId()));
    }

    @GetMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR', 'VIEWER')")
    public List<RobotRouteSummaryResponse> getRobotRoutes(
            @RequestParam(value = "robotId", required = false) Long robotId,
            @RequestParam(value = "routeStatus", required = false) RobotRouteStatus routeStatus
    ) {
        return robotRouteService.findAll(robotId, routeStatus).stream()
                .map(RobotRouteSummaryResponse::from)
                .toList();
    }

    @GetMapping("/{routeId}")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR', 'VIEWER')")
    public RobotRouteResponse getRobotRoute(@PathVariable Long routeId) {
        return RobotRouteResponse.from(
                robotRouteService.get(routeId),
                robotRouteService.getPoints(routeId)
        );
    }

    @PutMapping("/{routeId}")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public RobotRouteResponse updateRobotRoute(
            @PathVariable Long routeId,
            @Valid @RequestBody UpdateRobotRouteRequest request
    ) {
        var route = robotRouteService.update(
                routeId,
                request.name(),
                request.routeStatus(),
                request.points()
        );
        return RobotRouteResponse.from(route, robotRouteService.getPoints(routeId));
    }

    @DeleteMapping("/{routeId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public void deleteRobotRoute(@PathVariable Long routeId) {
        robotRouteService.delete(routeId);
    }
}
