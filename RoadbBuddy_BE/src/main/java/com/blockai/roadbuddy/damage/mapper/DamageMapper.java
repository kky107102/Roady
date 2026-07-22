package com.blockai.roadbuddy.damage.mapper;

import com.blockai.roadbuddy.damage.domain.Damage;
import com.blockai.roadbuddy.damage.domain.DamageImage;
import com.blockai.roadbuddy.damage.domain.DamageImageMetadata;
import com.blockai.roadbuddy.damage.domain.DamageSummary;
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
public interface DamageMapper {

    @Insert("""
            INSERT INTO damages (
                robot_id,
                reported_by,
                assigned_to,
                description,
                latitude,
                longitude,
                captured_at,
                current_status
            )
            VALUES (
                #{robotId},
                #{reportedBy},
                #{assignedTo},
                #{description},
                #{latitude},
                #{longitude},
                #{capturedAt},
                #{currentStatus}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insertDamage(Damage damage);

    @Insert("""
            INSERT INTO damage_images (
                damage_id,
                sort_order,
                original_filename,
                content_type,
                size_bytes,
                data
            )
            VALUES (
                #{damageId},
                #{sortOrder},
                #{originalFilename},
                #{contentType},
                #{sizeBytes},
                #{data}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insertImage(DamageImage image);

    @Select("""
            SELECT
                d.id,
                d.robot_id,
                d.reported_by,
                d.assigned_to,
                d.description,
                d.latitude,
                d.longitude,
                d.captured_at,
                d.current_status,
                COUNT(di.id) AS image_count,
                d.created_at,
                d.updated_at
            FROM damages d
            LEFT JOIN damage_images di ON di.damage_id = d.id
            WHERE d.id = #{id}
            GROUP BY
                d.id,
                d.robot_id,
                d.reported_by,
                d.assigned_to,
                d.description,
                d.latitude,
                d.longitude,
                d.captured_at,
                d.current_status,
                d.created_at,
                d.updated_at
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "reported_by", javaType = Long.class),
            @Arg(column = "assigned_to", javaType = Long.class),
            @Arg(column = "description", javaType = String.class),
            @Arg(column = "latitude", javaType = BigDecimal.class),
            @Arg(column = "longitude", javaType = BigDecimal.class),
            @Arg(column = "captured_at", javaType = LocalDateTime.class),
            @Arg(column = "current_status", javaType = String.class),
            @Arg(column = "image_count", javaType = long.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class),
            @Arg(column = "updated_at", javaType = LocalDateTime.class)
    })
    DamageSummary findSummaryById(@Param("id") Long id);

    @Select("""
            SELECT
                d.id,
                d.robot_id,
                d.reported_by,
                d.assigned_to,
                d.description,
                d.latitude,
                d.longitude,
                d.captured_at,
                d.current_status,
                COUNT(di.id) AS image_count,
                d.created_at,
                d.updated_at
            FROM damages d
            LEFT JOIN damage_images di ON di.damage_id = d.id
            GROUP BY
                d.id,
                d.robot_id,
                d.reported_by,
                d.assigned_to,
                d.description,
                d.latitude,
                d.longitude,
                d.captured_at,
                d.current_status,
                d.created_at,
                d.updated_at
            ORDER BY d.created_at DESC, d.id DESC
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "reported_by", javaType = Long.class),
            @Arg(column = "assigned_to", javaType = Long.class),
            @Arg(column = "description", javaType = String.class),
            @Arg(column = "latitude", javaType = BigDecimal.class),
            @Arg(column = "longitude", javaType = BigDecimal.class),
            @Arg(column = "captured_at", javaType = LocalDateTime.class),
            @Arg(column = "current_status", javaType = String.class),
            @Arg(column = "image_count", javaType = long.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class),
            @Arg(column = "updated_at", javaType = LocalDateTime.class)
    })
    List<DamageSummary> findAllSummaries();

    @Select("""
            SELECT id, damage_id, sort_order, original_filename, content_type, size_bytes, created_at
            FROM damage_images
            WHERE damage_id = #{damageId}
            ORDER BY sort_order ASC, id ASC
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "damage_id", javaType = Long.class),
            @Arg(column = "sort_order", javaType = int.class),
            @Arg(column = "original_filename", javaType = String.class),
            @Arg(column = "content_type", javaType = String.class),
            @Arg(column = "size_bytes", javaType = long.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class)
    })
    List<DamageImageMetadata> findImageMetadataByDamageId(@Param("damageId") Long damageId);

    @Select("""
            SELECT id, damage_id, sort_order, original_filename, content_type, size_bytes, data, created_at
            FROM damage_images
            WHERE damage_id = #{damageId}
              AND id = #{imageId}
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "damage_id", javaType = Long.class),
            @Arg(column = "sort_order", javaType = int.class),
            @Arg(column = "original_filename", javaType = String.class),
            @Arg(column = "content_type", javaType = String.class),
            @Arg(column = "size_bytes", javaType = long.class),
            @Arg(column = "data", javaType = byte[].class),
            @Arg(column = "created_at", javaType = LocalDateTime.class)
    })
    DamageImage findImageById(@Param("damageId") Long damageId, @Param("imageId") Long imageId);

    @Select("""
            SELECT id, damage_id, sort_order, original_filename, content_type, size_bytes, data, created_at
            FROM damage_images
            WHERE damage_id = #{damageId}
            ORDER BY sort_order ASC, id ASC
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "damage_id", javaType = Long.class),
            @Arg(column = "sort_order", javaType = int.class),
            @Arg(column = "original_filename", javaType = String.class),
            @Arg(column = "content_type", javaType = String.class),
            @Arg(column = "size_bytes", javaType = long.class),
            @Arg(column = "data", javaType = byte[].class),
            @Arg(column = "created_at", javaType = LocalDateTime.class)
    })
    List<DamageImage> findImagesByDamageId(@Param("damageId") Long damageId);
}
