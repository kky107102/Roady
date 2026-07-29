package com.blockai.roady.statistics.mapper;

import com.blockai.roady.statistics.domain.DamageTimeSeriesRow;
import com.blockai.roady.statistics.domain.StatisticsCountRow;
import com.blockai.roady.statistics.domain.RepairCompletionCounts;
import org.apache.ibatis.annotations.Arg;
import org.apache.ibatis.annotations.ConstructorArgs;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface StatisticsMapper {

    @Select("""
            <script>
            SELECT
                <choose>
                    <when test="unit == 'DAY'">
                        DATE_FORMAT(d.created_at, '%Y-%m-%d')
                    </when>
                    <when test="unit == 'WEEK'">
                        DATE_FORMAT(
                            DATE_SUB(DATE(d.created_at), INTERVAL WEEKDAY(d.created_at) DAY),
                            '%Y-%m-%d'
                        )
                    </when>
                    <when test="unit == 'MONTH'">
                        DATE_FORMAT(d.created_at, '%Y-%m')
                    </when>
                    <otherwise>
                        DATE_FORMAT(d.created_at, '%Y')
                    </otherwise>
                </choose>
                AS period_key,
                COUNT(*) AS total_count,
                SUM(
                    CASE WHEN d.current_status = 'REPAIR_COMPLETED' THEN 1 ELSE 0 END
                ) AS repair_completed_count
            FROM damages d
            WHERE d.created_at <![CDATA[>=]]> #{from}
              AND d.created_at <![CDATA[<]]> #{to}
            GROUP BY period_key
            ORDER BY period_key
            </script>
            """)
    @ConstructorArgs({
            @Arg(column = "period_key", javaType = String.class, id = true),
            @Arg(column = "total_count", javaType = long.class),
            @Arg(column = "repair_completed_count", javaType = long.class)
    })
    List<DamageTimeSeriesRow> findDamageTimeSeries(
            @Param("from") LocalDateTime from,
            @Param("to") LocalDateTime to,
            @Param("unit") String unit
    );

    @Select("""
            SELECT
                d.current_status AS category,
                COUNT(*) AS category_count
            FROM damages d
            WHERE d.created_at >= #{from}
              AND d.created_at < #{to}
            GROUP BY d.current_status
            """)
    @ConstructorArgs({
            @Arg(column = "category", javaType = String.class, id = true),
            @Arg(column = "category_count", javaType = long.class)
    })
    List<StatisticsCountRow> countDamagesByStatus(
            @Param("from") LocalDateTime from,
            @Param("to") LocalDateTime to
    );

    @Select("""
            SELECT
                CASE
                    WHEN ai.repair_priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')
                        THEN ai.repair_priority
                    ELSE 'UNCLASSIFIED'
                END AS category,
                COUNT(*) AS category_count
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
            WHERE d.created_at >= #{from}
              AND d.created_at < #{to}
            GROUP BY category
            """)
    @ConstructorArgs({
            @Arg(column = "category", javaType = String.class, id = true),
            @Arg(column = "category_count", javaType = long.class)
    })
    List<StatisticsCountRow> countDamagesByRepairPriority(
            @Param("from") LocalDateTime from,
            @Param("to") LocalDateTime to
    );

    @Select("""
            SELECT
                COUNT(*) AS total_count,
                COALESCE(
                    SUM(CASE WHEN d.current_status = 'REPAIR_COMPLETED' THEN 1 ELSE 0 END),
                    0
                ) AS completed_count,
                COALESCE(
                    SUM(CASE WHEN d.current_status = 'REPAIR_NOT_REQUIRED' THEN 1 ELSE 0 END),
                    0
                ) AS not_required_count
            FROM damages d
            WHERE d.created_at >= #{from}
              AND d.created_at < #{to}
            """)
    @ConstructorArgs({
            @Arg(column = "total_count", javaType = long.class),
            @Arg(column = "completed_count", javaType = long.class),
            @Arg(column = "not_required_count", javaType = long.class)
    })
    RepairCompletionCounts countRepairCompletion(
            @Param("from") LocalDateTime from,
            @Param("to") LocalDateTime to
    );
}
