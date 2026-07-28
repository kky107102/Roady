package com.blockai.roady.robot.service;

import com.blockai.roady.robot.domain.RobotConnectionStatus;
import com.blockai.roady.robot.domain.RobotStatus;
import com.blockai.roady.robot.domain.RobotStatusLog;
import com.blockai.roady.robot.mapper.RobotMapper;
import com.blockai.roady.robot.mapper.RobotStatusLogMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
public class RobotStatusLogService {

    private final RobotStatusLogMapper robotStatusLogMapper;
    private final RobotMapper robotMapper;
    private final RobotService robotService;

    public RobotStatusLogService(
            RobotStatusLogMapper robotStatusLogMapper,
            RobotMapper robotMapper,
            RobotService robotService
    ) {
        this.robotStatusLogMapper = robotStatusLogMapper;
        this.robotMapper = robotMapper;
        this.robotService = robotService;
    }

    @Transactional
    public RobotStatusLog create(
            Long robotId,
            BigDecimal latitude,
            BigDecimal longitude,
            Integer batteryLevel,
            RobotStatus operationStatus,
            RobotConnectionStatus connectionStatus,
            String errorCode,
            String errorMessage,
            LocalDateTime recordedAt
    ) {
        robotService.get(robotId);

        RobotStatusLog statusLog = new RobotStatusLog();
        statusLog.setRobotId(robotId);
        statusLog.setLatitude(latitude);
        statusLog.setLongitude(longitude);
        statusLog.setBatteryLevel(batteryLevel);
        statusLog.setOperationStatus(operationStatus);
        statusLog.setConnectionStatus(connectionStatus);
        statusLog.setErrorCode(errorCode);
        statusLog.setErrorMessage(errorMessage);
        statusLog.setRecordedAt(Optional.ofNullable(recordedAt).orElseGet(LocalDateTime::now));

        robotStatusLogMapper.insert(statusLog);
        robotMapper.updateStatus(robotId, operationStatus);

        return Optional.ofNullable(robotStatusLogMapper.findById(statusLog.getId()))
                .orElseThrow(() -> new IllegalStateException("Created robot status log not found."));
    }

    @Transactional(readOnly = true)
    public Optional<RobotStatusLog> findLatestByRobotId(Long robotId) {
        robotService.get(robotId);
        return Optional.ofNullable(robotStatusLogMapper.findLatestByRobotId(robotId));
    }

    @Transactional(readOnly = true)
    public Optional<RobotStatusLog> findLatestByRobotIdIfExists(Long robotId) {
        return Optional.ofNullable(robotStatusLogMapper.findLatestByRobotId(robotId));
    }

    @Transactional(readOnly = true)
    public List<RobotStatusLog> findByRobotId(Long robotId) {
        robotService.get(robotId);
        return robotStatusLogMapper.findByRobotId(robotId);
    }
}
