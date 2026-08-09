package com.blockai.roady.robot.mapper;

import com.blockai.roady.robot.domain.RobotRoute;
import com.blockai.roady.robot.domain.RobotRoutePoint;
import com.blockai.roady.robot.domain.RobotRoutePointType;
import com.blockai.roady.robot.domain.RobotRouteStatus;
import org.apache.ibatis.annotations.Arg;
import org.apache.ibatis.annotations.ConstructorArgs;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface RobotRouteMapper {

    @Insert("""
            INSERT INTO robot_routes (
                robot_id,
                created_by,
                name,
                route_status
            )
            VALUES (
                #{robotId},
                #{createdBy},
                #{name},
                #{routeStatus}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insertRoute(RobotRoute route);

    @Insert("""
            INSERT INTO robot_route_points (
                route_id,
                point_order,
                latitude,
                longitude,
                point_type
            )
            VALUES (
                #{routeId},
                #{pointOrder},
                #{latitude},
                #{longitude},
                #{pointType}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insertPoint(RobotRoutePoint point);

    @Select("""
            SELECT id, robot_id, created_by, name, route_status, created_at, updated_at
            FROM robot_routes
            WHERE id = #{id}
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "created_by", javaType = Long.class),
            @Arg(column = "name", javaType = String.class),
            @Arg(column = "route_status", javaType = RobotRouteStatus.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class),
            @Arg(column = "updated_at", javaType = LocalDateTime.class)
    })
    RobotRoute findById(@Param("id") Long id);

    @Select("""
            <script>
            SELECT id, robot_id, created_by, name, route_status, created_at, updated_at
            FROM robot_routes
            WHERE 1 = 1
            <if test="robotId != null">
              AND robot_id = #{robotId}
            </if>
            <if test="routeStatus != null">
              AND route_status = #{routeStatus}
            </if>
            ORDER BY created_at DESC, id DESC
            </script>
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "created_by", javaType = Long.class),
            @Arg(column = "name", javaType = String.class),
            @Arg(column = "route_status", javaType = RobotRouteStatus.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class),
            @Arg(column = "updated_at", javaType = LocalDateTime.class)
    })
    List<RobotRoute> findAll(
            @Param("robotId") Long robotId,
            @Param("routeStatus") RobotRouteStatus routeStatus
    );

    @Select("""
            SELECT id, route_id, point_order, latitude, longitude, point_type, created_at
            FROM robot_route_points
            WHERE route_id = #{routeId}
            ORDER BY point_order ASC, id ASC
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "route_id", javaType = Long.class),
            @Arg(column = "point_order", javaType = Integer.class),
            @Arg(column = "latitude", javaType = BigDecimal.class),
            @Arg(column = "longitude", javaType = BigDecimal.class),
            @Arg(column = "point_type", javaType = RobotRoutePointType.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class)
    })
    List<RobotRoutePoint> findPointsByRouteId(@Param("routeId") Long routeId);

    @Update("""
            UPDATE robot_routes
            SET
                name = #{name},
                route_status = #{routeStatus}
            WHERE id = #{id}
            """)
    int updateRoute(
            @Param("id") Long id,
            @Param("name") String name,
            @Param("routeStatus") RobotRouteStatus routeStatus
    );

    @Delete("DELETE FROM robot_route_points WHERE route_id = #{routeId}")
    int deletePointsByRouteId(@Param("routeId") Long routeId);

    @Delete("DELETE FROM robot_routes WHERE id = #{id}")
    int deleteRoute(@Param("id") Long id);
}
