package com.blockai.roady.robot.service;

import com.blockai.roady.robot.domain.Robot;
import com.blockai.roady.robot.domain.RobotStatus;
import com.blockai.roady.robot.mapper.RobotMapper;
import com.blockai.roady.user.service.UserAccountService;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.Optional;

@Service
public class RobotService {

    private final RobotMapper robotMapper;
    private final UserAccountService userAccountService;

    public RobotService(RobotMapper robotMapper, UserAccountService userAccountService) {
        this.robotMapper = robotMapper;
        this.userAccountService = userAccountService;
    }

    @Transactional
    public Robot create(Long userId, String name, String serialNumber) {
        validateResponsibleUser(userId);
        validateUniqueSerialNumber(serialNumber);

        Robot robot = new Robot();
        robot.setUserId(userId);
        robot.setName(name);
        robot.setSerialNumber(serialNumber);
        robot.setStatus(RobotStatus.STANDBY);
        robot.setActive(true);

        try {
            robotMapper.insert(robot);
        } catch (DuplicateKeyException ex) {
            throw new IllegalArgumentException("Already used robot serial number.");
        }

        return get(robot.getId());
    }

    @Transactional(readOnly = true)
    public List<Robot> findAll() {
        return robotMapper.findAll();
    }

    @Transactional(readOnly = true)
    public Robot get(Long robotId) {
        return Optional.ofNullable(robotMapper.findById(robotId))
                .orElseThrow(() -> new IllegalArgumentException("Robot not found."));
    }

    @Transactional
    public Robot update(Long robotId, Long userId, String name, Boolean active) {
        get(robotId);
        if (userId != null) {
            validateResponsibleUser(userId);
        }
        if (name != null && !StringUtils.hasText(name)) {
            throw new IllegalArgumentException("Robot name must not be blank.");
        }

        robotMapper.update(robotId, userId, name, active);
        return get(robotId);
    }

    @Transactional
    public Robot updateActive(Long robotId, boolean active) {
        int updatedRows = robotMapper.updateActive(robotId, active);
        if (updatedRows == 0) {
            throw new IllegalArgumentException("Robot not found.");
        }
        return get(robotId);
    }

    private void validateResponsibleUser(Long userId) {
        if (userAccountService.findById(userId).isEmpty()) {
            throw new IllegalArgumentException("Responsible user not found.");
        }
    }

    private void validateUniqueSerialNumber(String serialNumber) {
        if (robotMapper.existsBySerialNumber(serialNumber)) {
            throw new IllegalArgumentException("Already used robot serial number.");
        }
    }
}
