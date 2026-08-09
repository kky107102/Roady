package com.blockai.roady.damage.mapper;

import com.blockai.roady.damage.domain.DamageAiAnalysisResult;
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
public interface DamageAiAnalysisResultMapper {

    @Insert("""
            INSERT INTO damage_ai_analysis_results (
                damage_id,
                analysis_status
            )
            VALUES (
                #{damageId},
                #{analysisStatus}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(DamageAiAnalysisResult result);

    @Select("""
            SELECT
                id,
                damage_id,
                damaged,
                damage_score,
                damage_type,
                repair_required,
                repair_priority,
                confidence_score,
                analysis_status,
                raw_result,
                analyzed_at,
                created_at
            FROM damage_ai_analysis_results
            WHERE id = #{id}
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "damage_id", javaType = Long.class),
            @Arg(column = "damaged", javaType = Boolean.class),
            @Arg(column = "damage_score", javaType = Integer.class),
            @Arg(column = "damage_type", javaType = String.class),
            @Arg(column = "repair_required", javaType = Boolean.class),
            @Arg(column = "repair_priority", javaType = String.class),
            @Arg(column = "confidence_score", javaType = BigDecimal.class),
            @Arg(column = "analysis_status", javaType = String.class),
            @Arg(column = "raw_result", javaType = String.class),
            @Arg(column = "analyzed_at", javaType = LocalDateTime.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class)
    })
    DamageAiAnalysisResult findById(@Param("id") Long id);

    @Select("""
            SELECT
                id,
                damage_id,
                damaged,
                damage_score,
                damage_type,
                repair_required,
                repair_priority,
                confidence_score,
                analysis_status,
                raw_result,
                analyzed_at,
                created_at
            FROM damage_ai_analysis_results
            WHERE damage_id = #{damageId}
            ORDER BY created_at DESC, id DESC
            """)
    @ConstructorArgs({
            @Arg(column = "id", javaType = Long.class, id = true),
            @Arg(column = "damage_id", javaType = Long.class),
            @Arg(column = "damaged", javaType = Boolean.class),
            @Arg(column = "damage_score", javaType = Integer.class),
            @Arg(column = "damage_type", javaType = String.class),
            @Arg(column = "repair_required", javaType = Boolean.class),
            @Arg(column = "repair_priority", javaType = String.class),
            @Arg(column = "confidence_score", javaType = BigDecimal.class),
            @Arg(column = "analysis_status", javaType = String.class),
            @Arg(column = "raw_result", javaType = String.class),
            @Arg(column = "analyzed_at", javaType = LocalDateTime.class),
            @Arg(column = "created_at", javaType = LocalDateTime.class)
    })
    List<DamageAiAnalysisResult> findByDamageId(@Param("damageId") Long damageId);

    @Update("""
            UPDATE damage_ai_analysis_results
            SET analysis_status = 'PROCESSING'
            WHERE id = #{id}
            """)
    int markProcessing(@Param("id") Long id);

    @Update("""
            UPDATE damage_ai_analysis_results
            SET damaged = #{damaged},
                damage_score = #{damageScore},
                damage_type = #{damageType},
                repair_required = #{repairRequired},
                repair_priority = #{repairPriority},
                confidence_score = #{confidenceScore},
                analysis_status = 'SUCCESS',
                raw_result = #{rawResult},
                analyzed_at = CURRENT_TIMESTAMP(6)
            WHERE id = #{id}
            """)
    int markSucceeded(
            @Param("id") Long id,
            @Param("damaged") Boolean damaged,
            @Param("damageScore") Integer damageScore,
            @Param("damageType") String damageType,
            @Param("repairRequired") Boolean repairRequired,
            @Param("repairPriority") String repairPriority,
            @Param("confidenceScore") BigDecimal confidenceScore,
            @Param("rawResult") String rawResult
    );

    @Update("""
            UPDATE damage_ai_analysis_results
            SET analysis_status = 'FAILED',
                raw_result = #{rawResult},
                analyzed_at = CURRENT_TIMESTAMP(6)
            WHERE id = #{id}
            """)
    int markFailed(@Param("id") Long id, @Param("rawResult") String rawResult);
}
