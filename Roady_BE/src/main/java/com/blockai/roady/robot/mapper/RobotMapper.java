package com.blockai.roady.robot.mapper;

import com.blockai.roady.robot.domain.Robot;
import com.blockai.roady.robot.domain.RobotStatus;
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
public interface RobotMapper {

    @Insert("""
            INSERT INTO robots (user_id, name, serial_number, status, active)
            VALUES (#{userId}, #{name}, #{serialNumber}, #{status}, #{active})
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Robot robot);

    @Select("""
            SELECT id, user_id, name, serial_number, status, active, created_at, updated_at
            FROM robots
            WHERE id = #{id}
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "user_id", javaType = Long.class),
            @Arg(column = "name", javaType = String.class),
            @Arg(column = "serial_number", javaType = String.class),
            @Arg(column = "status", javaType = RobotStatus.class),
            @Arg(column = "active", javaType = boolean.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class),
            @Arg(column = "updated_at", javaType = LocalDateTime.class)
    })
    Robot findById(@Param("id") Long id);

    @Select("""
            SELECT id, user_id, name, serial_number, status, active, created_at, updated_at
            FROM robots
            ORDER BY created_at DESC, id DESC
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "user_id", javaType = Long.class),
            @Arg(column = "name", javaType = String.class),
            @Arg(column = "serial_number", javaType = String.class),
            @Arg(column = "status", javaType = RobotStatus.class),
            @Arg(column = "active", javaType = boolean.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class),
            @Arg(column = "updated_at", javaType = LocalDateTime.class)
    })
    List<Robot> findAll();

    @Select("SELECT COUNT(*) > 0 FROM robots WHERE serial_number = #{serialNumber}")
    boolean existsBySerialNumber(@Param("serialNumber") String serialNumber);

    @Update("""
            UPDATE robots
            SET
                user_id = COALESCE(#{userId}, user_id),
                name = COALESCE(#{name}, name),
                active = COALESCE(#{active}, active)
            WHERE id = #{id}
            """)
    int update(
            @Param("id") Long id,
            @Param("userId") Long userId,
            @Param("name") String name,
            @Param("active") Boolean active
    );

    @Update("""
            UPDATE robots
            SET active = #{active}
            WHERE id = #{id}
            """)
    int updateActive(@Param("id") Long id, @Param("active") boolean active);

    @Update("""
            UPDATE robots
            SET status = #{status}
            WHERE id = #{id}
            """)
    int updateStatus(@Param("id") Long id, @Param("status") RobotStatus status);
}
