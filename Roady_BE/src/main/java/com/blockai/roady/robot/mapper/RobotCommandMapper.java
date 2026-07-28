package com.blockai.roady.robot.mapper;

import com.blockai.roady.robot.domain.RobotCommand;
import com.blockai.roady.robot.domain.RobotCommandStatus;
import com.blockai.roady.robot.domain.RobotCommandType;
import org.apache.ibatis.annotations.Arg;
import org.apache.ibatis.annotations.ConstructorArgs;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface RobotCommandMapper {

    @Insert("""
            INSERT INTO robot_commands (
                robot_id,
                requested_by,
                command_type,
                command_status
            )
            VALUES (
                #{robotId},
                #{requestedBy},
                #{commandType},
                #{commandStatus}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(RobotCommand command);

    @Select("""
            SELECT id, robot_id, requested_by, command_type, command_status, requested_at
            FROM robot_commands
            WHERE id = #{id}
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "requested_by", javaType = Long.class),
            @Arg(column = "command_type", javaType = RobotCommandType.class),
            @Arg(column = "command_status", javaType = RobotCommandStatus.class),
            @Arg(column = "requested_at", javaType = LocalDateTime.class)
    })
    RobotCommand findById(@Param("id") Long id);

    @Select("""
            SELECT id, robot_id, requested_by, command_type, command_status, requested_at
            FROM robot_commands
            WHERE robot_id = #{robotId}
            ORDER BY requested_at DESC, id DESC
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "requested_by", javaType = Long.class),
            @Arg(column = "command_type", javaType = RobotCommandType.class),
            @Arg(column = "command_status", javaType = RobotCommandStatus.class),
            @Arg(column = "requested_at", javaType = LocalDateTime.class)
    })
    List<RobotCommand> findByRobotId(@Param("robotId") Long robotId);
}
