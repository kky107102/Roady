package com.blockai.roady.robot.service;

import com.blockai.roady.robot.domain.RobotConnectionStatus;
import com.blockai.roady.robot.domain.RobotStatusLog;
import com.blockai.roady.robot.mapper.RobotMapper;
import com.blockai.roady.robot.mapper.RobotStatusLogMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Optional;

@Service
public class RobotConnectionStatusService {

    private static final Logger log = LoggerFactory.getLogger(RobotConnectionStatusService.class);

    private final RobotStatusLogMapper robotStatusLogMapper;
    private final RobotMapper robotMapper;
    private final RobotService robotService;

    public RobotConnectionStatusService(
            RobotStatusLogMapper robotStatusLogMapper,
            RobotMapper robotMapper,
            RobotService robotService
    ) {
        this.robotStatusLogMapper = robotStatusLogMapper;
        this.robotMapper = robotMapper;
        this.robotService = robotService;
    }

    @Transactional
    public Optional<RobotStatusLog> updateConnectionStatus(Long robotId, RobotConnectionStatus connectionStatus) {
        robotService.get(robotId);

        RobotStatusLog latest = robotStatusLogMapper.findLatestByRobotId(robotId);
        if (latest == null) {
            log.warn("Robot {} has no status log. Connection status {} was not recorded.", robotId, connectionStatus);
            return Optional.empty();
        }
        if (latest.getConnectionStatus() == connectionStatus) {
            return Optional.of(latest);
        }

        RobotStatusLog statusLog = new RobotStatusLog();
        statusLog.setRobotId(robotId);
        statusLog.setLatitude(latest.getLatitude());
        statusLog.setLongitude(latest.getLongitude());
        statusLog.setBatteryLevel(latest.getBatteryLevel());
        statusLog.setOperationStatus(latest.getOperationStatus());
        statusLog.setConnectionStatus(connectionStatus);
        statusLog.setErrorCode(latest.getErrorCode());
        statusLog.setErrorMessage(latest.getErrorMessage());
        statusLog.setRecordedAt(LocalDateTime.now());

        robotStatusLogMapper.insert(statusLog);
        robotMapper.updateStatus(robotId, latest.getOperationStatus());

        return Optional.ofNullable(robotStatusLogMapper.findById(statusLog.getId()));
    }
}
