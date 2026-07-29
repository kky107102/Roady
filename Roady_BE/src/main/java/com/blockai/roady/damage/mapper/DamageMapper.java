package com.blockai.roady.damage.mapper;

import com.blockai.roady.damage.domain.Damage;
import com.blockai.roady.damage.domain.DamageImage;
import com.blockai.roady.damage.domain.DamageImageMetadata;
import com.blockai.roady.damage.domain.DamageMapMarker;
import com.blockai.roady.damage.domain.DamageSearchItem;
import com.blockai.roady.damage.domain.DamageStatusCount;
import com.blockai.roady.damage.domain.DamageSummary;
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
            <script>
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
                (
                    SELECT COUNT(*)
                    FROM damage_images di
                    WHERE di.damage_id = d.id
                ) AS image_count,
                ai.damage_score,
                ai.repair_required,
                ai.repair_priority,
                ai.confidence_score,
                d.created_at
            FROM damages d
            LEFT JOIN damage_ai_analysis_results ai
                ON ai.id = (
                    SELECT latest_ai.id
                    FROM damage_ai_analysis_results latest_ai
                    WHERE latest_ai.damage_id = d.id
                      AND latest_ai.analysis_status = 'SUCCESS'
                    ORDER BY latest_ai.created_at DESC, latest_ai.id DESC
                    LIMIT 1
                )
            <where>
                <if test="from != null">
                    AND d.created_at <![CDATA[>=]]> #{from}
                </if>
                <if test="to != null">
                    AND d.created_at <![CDATA[<]]> #{to}
                </if>
                <if test="status != null">
                    AND d.current_status = #{status}
                </if>
                <if test="robotId != null">
                    AND d.robot_id = #{robotId}
                </if>
                <if test="assignedTo != null">
                    AND d.assigned_to = #{assignedTo}
                </if>
            </where>
            ORDER BY d.created_at DESC, d.id DESC
            LIMIT #{offset}, #{size}
            </script>
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "assigned_to", javaType = Long.class),
            @Arg(column = "description", javaType = String.class),
            @Arg(column = "latitude", javaType = BigDecimal.class),
            @Arg(column = "longitude", javaType = BigDecimal.class),
            @Arg(column = "captured_at", javaType = LocalDateTime.class),
            @Arg(column = "current_status", javaType = String.class),
            @Arg(column = "image_count", javaType = long.class),
            @Arg(column = "damage_score", javaType = Integer.class),
            @Arg(column = "repair_required", javaType = Boolean.class),
            @Arg(column = "repair_priority", javaType = String.class),
            @Arg(column = "confidence_score", javaType = BigDecimal.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class)
    })
    List<DamageSearchItem> searchSummaries(
            @Param("from") LocalDateTime from,
            @Param("to") LocalDateTime to,
            @Param("status") String status,
            @Param("robotId") Long robotId,
            @Param("assignedTo") Long assignedTo,
            @Param("offset") long offset,
            @Param("size") int size
    );

    @Select("""
            <script>
            SELECT COUNT(*)
            FROM damages d
            <where>
                <if test="from != null">
                    AND d.created_at <![CDATA[>=]]> #{from}
                </if>
                <if test="to != null">
                    AND d.created_at <![CDATA[<]]> #{to}
                </if>
                <if test="status != null">
                    AND d.current_status = #{status}
                </if>
                <if test="robotId != null">
                    AND d.robot_id = #{robotId}
                </if>
                <if test="assignedTo != null">
                    AND d.assigned_to = #{assignedTo}
                </if>
            </where>
            </script>
            """)
    long countSummaries(
            @Param("from") LocalDateTime from,
            @Param("to") LocalDateTime to,
            @Param("status") String status,
            @Param("robotId") Long robotId,
            @Param("assignedTo") Long assignedTo
    );

    @Select("""
            <script>
            SELECT
                d.current_status,
                COUNT(*) AS total,
                SUM(CASE WHEN d.assigned_to IS NULL THEN 1 ELSE 0 END) AS unassigned
            FROM damages d
            <where>
                <if test="from != null">
                    AND d.created_at <![CDATA[>=]]> #{from}
                </if>
                <if test="to != null">
                    AND d.created_at <![CDATA[<]]> #{to}
                </if>
                <if test="status != null">
                    AND d.current_status = #{status}
                </if>
                <if test="robotId != null">
                    AND d.robot_id = #{robotId}
                </if>
                <if test="assignedTo != null">
                    AND d.assigned_to = #{assignedTo}
                </if>
            </where>
            GROUP BY d.current_status
            </script>
            """)
    @ConstructorArgs({
            @Arg(column = "current_status", javaType = String.class, id = true),
            @Arg(column = "total", javaType = long.class),
            @Arg(column = "unassigned", javaType = long.class)
    })
    List<DamageStatusCount> summarizeByStatus(
            @Param("from") LocalDateTime from,
            @Param("to") LocalDateTime to,
            @Param("status") String status,
            @Param("robotId") Long robotId,
            @Param("assignedTo") Long assignedTo
    );

    @Select("""
            <script>
            SELECT
                d.id,
                d.latitude,
                d.longitude,
                d.current_status
            FROM damages d
            <where>
                AND d.latitude BETWEEN #{south} AND #{north}
                AND d.longitude BETWEEN #{west} AND #{east}
                <if test="from != null">
                    AND d.created_at <![CDATA[>=]]> #{from}
                </if>
                <if test="to != null">
                    AND d.created_at <![CDATA[<]]> #{to}
                </if>
                <if test="status != null">
                    AND d.current_status = #{status}
                </if>
                <if test="robotId != null">
                    AND d.robot_id = #{robotId}
                </if>
                <if test="assignedTo != null">
                    AND d.assigned_to = #{assignedTo}
                </if>
            </where>
            ORDER BY d.created_at DESC, d.id DESC
            </script>
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "latitude", javaType = BigDecimal.class),
            @Arg(column = "longitude", javaType = BigDecimal.class),
            @Arg(column = "current_status", javaType = String.class)
    })
    List<DamageMapMarker> findMapMarkers(
            @Param("from") LocalDateTime from,
            @Param("to") LocalDateTime to,
            @Param("status") String status,
            @Param("robotId") Long robotId,
            @Param("assignedTo") Long assignedTo,
            @Param("south") BigDecimal south,
            @Param("north") BigDecimal north,
            @Param("west") BigDecimal west,
            @Param("east") BigDecimal east
    );

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
