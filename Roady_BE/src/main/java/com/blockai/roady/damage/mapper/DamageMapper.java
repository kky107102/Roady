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
import org.apache.ibatis.annotations.Update;

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
                address_name,
                road_address_name,
                region_code,
                region_1depth_name,
                region_2depth_name,
                region_3depth_name,
                geocoded_at,
                latitude,
                longitude,
                captured_at,
                current_status,
                processing_priority
            )
            VALUES (
                #{robotId},
                #{reportedBy},
                #{assignedTo},
                #{description},
                #{addressName},
                #{roadAddressName},
                #{regionCode},
                #{region1DepthName},
                #{region2DepthName},
                #{region3DepthName},
                #{geocodedAt},
                #{latitude},
                #{longitude},
                #{capturedAt},
                #{currentStatus},
                #{processingPriority}
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
                d.address_name,
                d.road_address_name,
                d.region_code,
                d.region_1depth_name,
                d.region_2depth_name,
                d.region_3depth_name,
                d.geocoded_at,
                d.latitude,
                d.longitude,
                d.captured_at,
                d.current_status,
                d.processing_priority,
                d.review_damage_type,
                d.review_note,
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
                d.address_name,
                d.road_address_name,
                d.region_code,
                d.region_1depth_name,
                d.region_2depth_name,
                d.region_3depth_name,
                d.geocoded_at,
                d.latitude,
                d.longitude,
                d.captured_at,
                d.current_status,
                d.processing_priority,
                d.review_damage_type,
                d.review_note,
                d.created_at,
                d.updated_at
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "robot_id", javaType = Long.class),
            @Arg(column = "reported_by", javaType = Long.class),
            @Arg(column = "assigned_to", javaType = Long.class),
            @Arg(column = "description", javaType = String.class),
            @Arg(column = "address_name", javaType = String.class),
            @Arg(column = "road_address_name", javaType = String.class),
            @Arg(column = "region_code", javaType = String.class),
            @Arg(column = "region_1depth_name", javaType = String.class),
            @Arg(column = "region_2depth_name", javaType = String.class),
            @Arg(column = "region_3depth_name", javaType = String.class),
            @Arg(column = "geocoded_at", javaType = LocalDateTime.class),
            @Arg(column = "latitude", javaType = BigDecimal.class),
            @Arg(column = "longitude", javaType = BigDecimal.class),
            @Arg(column = "captured_at", javaType = LocalDateTime.class),
            @Arg(column = "current_status", javaType = String.class),
            @Arg(column = "processing_priority", javaType = String.class),
            @Arg(column = "review_damage_type", javaType = String.class),
            @Arg(column = "review_note", javaType = String.class),
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
                d.address_name,
                d.road_address_name,
                d.region_code,
                d.region_1depth_name,
                d.region_2depth_name,
                d.region_3depth_name,
                d.geocoded_at,
                d.latitude,
                d.longitude,
                d.captured_at,
                d.current_status,
                d.processing_priority,
                d.review_damage_type,
                d.review_note,
                (
                    SELECT COUNT(*)
                    FROM damage_images di
                    WHERE di.damage_id = d.id
                ) AS image_count,
                ai.damage_score,
                ai.damage_type,
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
                <if test="regionCode != null">
                    AND d.region_code = #{regionCode}
                </if>
                <if test="caseNumber != null or addressKeyword != null">
                    AND (
                        <if test="caseNumber != null">
                            d.id = #{caseNumber}
                        </if>
                        <if test="caseNumber != null and addressKeyword != null">
                            OR
                        </if>
                        <if test="addressKeyword != null">
                            d.address_name LIKE CONCAT('%', #{addressKeyword}, '%') ESCAPE '\\\\'
                            OR d.road_address_name LIKE CONCAT('%', #{addressKeyword}, '%') ESCAPE '\\\\'
                        </if>
                    )
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
            @Arg(column = "address_name", javaType = String.class),
            @Arg(column = "road_address_name", javaType = String.class),
            @Arg(column = "region_code", javaType = String.class),
            @Arg(column = "region_1depth_name", javaType = String.class),
            @Arg(column = "region_2depth_name", javaType = String.class),
            @Arg(column = "region_3depth_name", javaType = String.class),
            @Arg(column = "geocoded_at", javaType = LocalDateTime.class),
            @Arg(column = "latitude", javaType = BigDecimal.class),
            @Arg(column = "longitude", javaType = BigDecimal.class),
            @Arg(column = "captured_at", javaType = LocalDateTime.class),
            @Arg(column = "current_status", javaType = String.class),
            @Arg(column = "processing_priority", javaType = String.class),
            @Arg(column = "review_damage_type", javaType = String.class),
            @Arg(column = "review_note", javaType = String.class),
            @Arg(column = "image_count", javaType = long.class),
            @Arg(column = "damage_score", javaType = Integer.class),
            @Arg(column = "damage_type", javaType = String.class),
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
            @Param("regionCode") String regionCode,
            @Param("caseNumber") Long caseNumber,
            @Param("addressKeyword") String addressKeyword,
            @Param("offset") long offset,
            @Param("size") int size
    );

    @Update("""
            UPDATE damages
            SET
                current_status = #{status},
                processing_priority = #{processingPriority},
                review_damage_type = #{reviewDamageType},
                review_note = #{reviewNote}
            WHERE id = #{damageId}
            """)
    int updateReview(
            @Param("damageId") Long damageId,
            @Param("status") String status,
            @Param("processingPriority") String processingPriority,
            @Param("reviewDamageType") String reviewDamageType,
            @Param("reviewNote") String reviewNote
    );

    @Update("""
            UPDATE damages
            SET current_status = 'REPAIR_IN_PROGRESS'
            WHERE id = #{damageId}
              AND current_status = 'REQUESTED'
            """)
    int transitionToRepairInProgress(@Param("damageId") Long damageId);

    @Insert("""
            INSERT INTO repair_request_histories (
                damage_id,
                requested_by,
                before_status,
                after_status,
                note,
                requested_at
            )
            VALUES (
                #{damageId},
                #{requestedBy},
                #{beforeStatus},
                #{afterStatus},
                #{note},
                #{requestedAt}
            )
            """)
    int insertRepairRequestHistory(
            @Param("damageId") Long damageId,
            @Param("requestedBy") Long requestedBy,
            @Param("beforeStatus") String beforeStatus,
            @Param("afterStatus") String afterStatus,
            @Param("note") String note,
            @Param("requestedAt") LocalDateTime requestedAt
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
                <if test="regionCode != null">
                    AND d.region_code = #{regionCode}
                </if>
                <if test="caseNumber != null or addressKeyword != null">
                    AND (
                        <if test="caseNumber != null">
                            d.id = #{caseNumber}
                        </if>
                        <if test="caseNumber != null and addressKeyword != null">
                            OR
                        </if>
                        <if test="addressKeyword != null">
                            d.address_name LIKE CONCAT('%', #{addressKeyword}, '%') ESCAPE '\\\\'
                            OR d.road_address_name LIKE CONCAT('%', #{addressKeyword}, '%') ESCAPE '\\\\'
                        </if>
                    )
                </if>
            </where>
            </script>
            """)
    long countSummaries(
            @Param("from") LocalDateTime from,
            @Param("to") LocalDateTime to,
            @Param("status") String status,
            @Param("robotId") Long robotId,
            @Param("assignedTo") Long assignedTo,
            @Param("regionCode") String regionCode,
            @Param("caseNumber") Long caseNumber,
            @Param("addressKeyword") String addressKeyword
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
                <if test="regionCode != null">
                    AND d.region_code = #{regionCode}
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
            @Param("assignedTo") Long assignedTo,
            @Param("regionCode") String regionCode
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
                <if test="regionCode != null">
                    AND d.region_code = #{regionCode}
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
            @Param("regionCode") String regionCode,
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
