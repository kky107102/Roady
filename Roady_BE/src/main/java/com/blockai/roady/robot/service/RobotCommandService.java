package com.blockai.roady.robot.service;

import com.blockai.roady.robot.domain.RobotCommand;
import com.blockai.roady.robot.domain.RobotCommandStatus;
import com.blockai.roady.robot.domain.RobotCommandType;
import com.blockai.roady.robot.mapper.RobotCommandMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
public class RobotCommandService {

    private final RobotCommandMapper robotCommandMapper;
    private final RobotService robotService;

    public RobotCommandService(RobotCommandMapper robotCommandMapper, RobotService robotService) {
        this.robotCommandMapper = robotCommandMapper;
        this.robotService = robotService;
    }

    @Transactional
    public RobotCommand create(Long robotId, Long requestedBy, RobotCommandType commandType) {
        robotService.get(robotId);

        RobotCommand command = new RobotCommand();
        command.setRobotId(robotId);
        command.setRequestedBy(requestedBy);
        command.setCommandType(commandType);
        command.setCommandStatus(RobotCommandStatus.PENDING);
        robotCommandMapper.insert(command);

        return Optional.ofNullable(robotCommandMapper.findById(command.getId()))
                .orElseThrow(() -> new IllegalStateException("Created robot command not found."));
    }

    @Transactional(readOnly = true)
    public List<RobotCommand> findByRobotId(Long robotId) {
        robotService.get(robotId);
        return robotCommandMapper.findByRobotId(robotId);
    }
}
