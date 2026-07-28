package com.blockai.roady.robot.mapper;

import com.blockai.roady.robot.domain.RobotConnectionStatus;
import com.blockai.roady.robot.domain.RobotStatus;
import com.blockai.roady.robot.domain.RobotStatusLog;
import org.apache.ibatis.annotations.Arg;
import org.apache.ibatis.annotations.ConstructorArgs;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface RobotStatusLogMapper {

    @Insert("""
            INSERT INTO robot_status_logs (
                robot_id,
                latitude,
                longitude,
                battery_level,
                operation_status,
                connection_status,
                error_code,
                error_message,
                recorded_at
            )
            VALUES (
                #{robotId},
                #{latitude},
                #{longitude},
                #{batteryLevel},
                #{operationStatus},
                #{connectionStatus},
                #{errorCode},
                #{errorMessage},
                #{recordedAt}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(RobotStatusLog statusLog);

    @Select("""
            SELECT
                id,
                robot_id,
                latitude,
                longitude,
                battery_level,
                operation_status,
                connection_status,
                error_code,
                error_message,
                recorded_at
            FROM robot_status_logs
            WHERE id = #{id}
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "latitude", javaType = BigDecimal.class),
            @Arg(column = "longitude", javaType = BigDecimal.class),
            @Arg(column = "battery_level", javaType = Integer.class),
            @Arg(column = "operation_status", javaType = RobotStatus.class),
            @Arg(column = "connection_status", javaType = RobotConnectionStatus.class),
            @Arg(column = "error_code", javaType = String.class),
            @Arg(column = "error_message", javaType = String.class),
            @Arg(column = "recorded_at", javaType = LocalDateTime.class)
    })
    RobotStatusLog findById(@Param("id") Long id);

    @Select("""
            SELECT
                id,
                robot_id,
                latitude,
                longitude,
                battery_level,
                operation_status,
                connection_status,
                error_code,
                error_message,
                recorded_at
            FROM robot_status_logs
            WHERE robot_id = #{robotId}
            ORDER BY recorded_at DESC, id DESC
            LIMIT 1
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "latitude", javaType = BigDecimal.class),
            @Arg(column = "longitude", javaType = BigDecimal.class),
            @Arg(column = "battery_level", javaType = Integer.class),
            @Arg(column = "operation_status", javaType = RobotStatus.class),
            @Arg(column = "connection_status", javaType = RobotConnectionStatus.class),
            @Arg(column = "error_code", javaType = String.class),
            @Arg(column = "error_message", javaType = String.class),
            @Arg(column = "recorded_at", javaType = LocalDateTime.class)
    })
    RobotStatusLog findLatestByRobotId(@Param("robotId") Long robotId);

    @Select("""
            SELECT
                id,
                robot_id,
                latitude,
                longitude,
                battery_level,
                operation_status,
                connection_status,
                error_code,
                error_message,
                recorded_at
            FROM robot_status_logs
            WHERE robot_id = #{robotId}
            ORDER BY recorded_at DESC, id DESC
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "latitude", javaType = BigDecimal.class),
            @Arg(column = "longitude", javaType = BigDecimal.class),
            @Arg(column = "battery_level", javaType = Integer.class),
            @Arg(column = "operation_status", javaType = RobotStatus.class),
            @Arg(column = "connection_status", javaType = RobotConnectionStatus.class),
            @Arg(column = "error_code", javaType = String.class),
            @Arg(column = "error_message", javaType = String.class),
            @Arg(column = "recorded_at", javaType = LocalDateTime.class)
    })
    List<RobotStatusLog> findByRobotId(@Param("robotId") Long robotId);
}
