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
import org.apache.ibatis.annotations.Update;

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
            SELECT id, robot_id, requested_by, command_type, command_status, result_message, requested_at, completed_at
            FROM robot_commands
            WHERE id = #{id}
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "requested_by", javaType = Long.class),
            @Arg(column = "command_type", javaType = RobotCommandType.class),
            @Arg(column = "command_status", javaType = RobotCommandStatus.class),
            @Arg(column = "result_message", javaType = String.class),
            @Arg(column = "requested_at", javaType = LocalDateTime.class),
            @Arg(column = "completed_at", javaType = LocalDateTime.class)
    })
    RobotCommand findById(@Param("id") Long id);

    @Select("""
            SELECT id, robot_id, requested_by, command_type, command_status, result_message, requested_at, completed_at
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
            @Arg(column = "result_message", javaType = String.class),
            @Arg(column = "requested_at", javaType = LocalDateTime.class),
            @Arg(column = "completed_at", javaType = LocalDateTime.class)
    })
    List<RobotCommand> findByRobotId(@Param("robotId") Long robotId);

    @Select("""
            SELECT id, robot_id, requested_by, command_type, command_status, result_message, requested_at, completed_at
            FROM robot_commands
            WHERE robot_id = #{robotId}
              AND command_status = 'PENDING'
            ORDER BY requested_at ASC, id ASC
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "requested_by", javaType = Long.class),
            @Arg(column = "command_type", javaType = RobotCommandType.class),
            @Arg(column = "command_status", javaType = RobotCommandStatus.class),
            @Arg(column = "result_message", javaType = String.class),
            @Arg(column = "requested_at", javaType = LocalDateTime.class),
            @Arg(column = "completed_at", javaType = LocalDateTime.class)
    })
    List<RobotCommand> findPendingByRobotId(@Param("robotId") Long robotId);

    @Update("""
            UPDATE robot_commands
            SET
                command_status = #{commandStatus},
                result_message = #{resultMessage},
                completed_at = #{completedAt}
            WHERE id = #{id}
              AND robot_id = #{robotId}
            """)
    int updateStatus(
            @Param("id") Long id,
            @Param("robotId") Long robotId,
            @Param("commandStatus") RobotCommandStatus commandStatus,
            @Param("resultMessage") String resultMessage,
            @Param("completedAt") LocalDateTime completedAt
    );
}
