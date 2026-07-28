package com.blockai.roady.robot.service;

import com.blockai.roady.robot.domain.RobotRoute;
import com.blockai.roady.robot.domain.RobotRoutePoint;
import com.blockai.roady.robot.domain.RobotRoutePointType;
import com.blockai.roady.robot.domain.RobotRouteStatus;
import com.blockai.roady.robot.dto.RobotRoutePointRequest;
import com.blockai.roady.robot.mapper.RobotRouteMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashSet;
import java.util.List;
import java.util.Optional;

@Service
public class RobotRouteService {

    private static final int MIN_POINT_COUNT = 2;

    private final RobotRouteMapper robotRouteMapper;
    private final RobotService robotService;

    public RobotRouteService(RobotRouteMapper robotRouteMapper, RobotService robotService) {
        this.robotRouteMapper = robotRouteMapper;
        this.robotService = robotService;
    }

    @Transactional
    public RobotRoute create(Long robotId, Long createdBy, String name, List<RobotRoutePointRequest> points) {
        robotService.get(robotId);
        validatePoints(points);

        RobotRoute route = new RobotRoute();
        route.setRobotId(robotId);
        route.setCreatedBy(createdBy);
        route.setName(name);
        route.setRouteStatus(RobotRouteStatus.CREATED);
        robotRouteMapper.insertRoute(route);

        insertPoints(route.getId(), points);
        return get(route.getId());
    }

    @Transactional(readOnly = true)
    public List<RobotRoute> findAll(Long robotId, RobotRouteStatus routeStatus) {
        if (robotId != null) {
            robotService.get(robotId);
        }
        return robotRouteMapper.findAll(robotId, routeStatus);
    }

    @Transactional(readOnly = true)
    public RobotRoute get(Long routeId) {
        return Optional.ofNullable(robotRouteMapper.findById(routeId))
                .orElseThrow(() -> new IllegalArgumentException("Robot route not found."));
    }

    @Transactional(readOnly = true)
    public List<RobotRoutePoint> getPoints(Long routeId) {
        get(routeId);
        return robotRouteMapper.findPointsByRouteId(routeId);
    }

    @Transactional
    public RobotRoute update(
            Long routeId,
            String name,
            RobotRouteStatus routeStatus,
            List<RobotRoutePointRequest> points
    ) {
        RobotRoute route = get(routeId);
        validatePoints(points);

        RobotRouteStatus nextStatus = Optional.ofNullable(routeStatus).orElse(route.getRouteStatus());
        robotRouteMapper.updateRoute(routeId, name, nextStatus);
        robotRouteMapper.deletePointsByRouteId(routeId);
        insertPoints(routeId, points);

        return get(routeId);
    }

    @Transactional
    public void delete(Long routeId) {
        RobotRoute route = get(routeId);
        if (route.getRouteStatus() != RobotRouteStatus.CREATED) {
            throw new IllegalArgumentException("Only CREATED robot routes can be deleted.");
        }
        robotRouteMapper.deleteRoute(routeId);
    }

    private void insertPoints(Long routeId, List<RobotRoutePointRequest> points) {
        for (RobotRoutePointRequest request : points) {
            RobotRoutePoint point = new RobotRoutePoint();
            point.setRouteId(routeId);
            point.setPointOrder(request.pointOrder());
            point.setLatitude(request.latitude());
            point.setLongitude(request.longitude());
            point.setPointType(request.pointType());
            robotRouteMapper.insertPoint(point);
        }
    }

    private void validatePoints(List<RobotRoutePointRequest> points) {
        if (points == null || points.size() < MIN_POINT_COUNT) {
            throw new IllegalArgumentException("At least two route points are required.");
        }

        long startCount = points.stream()
                .filter(point -> point.pointType() == RobotRoutePointType.START)
                .count();
        long destinationCount = points.stream()
                .filter(point -> point.pointType() == RobotRoutePointType.DESTINATION)
                .count();

        if (startCount != 1) {
            throw new IllegalArgumentException("Exactly one START point is required.");
        }
        if (destinationCount != 1) {
            throw new IllegalArgumentException("Exactly one DESTINATION point is required.");
        }

        HashSet<Integer> orders = new HashSet<>();
        for (RobotRoutePointRequest point : points) {
            if (!orders.add(point.pointOrder())) {
                throw new IllegalArgumentException("Route point order must be unique.");
            }
        }
    }
}
