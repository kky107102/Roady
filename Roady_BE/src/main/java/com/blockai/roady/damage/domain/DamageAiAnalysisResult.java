package com.blockai.roady.damage.domain;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class DamageAiAnalysisResult {

    private Long id;
    private Long damageId;
    private Boolean damaged;
    private Integer damageScore;
    private String damageType;
    private Boolean repairRequired;
    private String repairPriority;
    private BigDecimal confidenceScore;
    private String analysisStatus;
    private String rawResult;
    private LocalDateTime analyzedAt;
    private LocalDateTime createdAt;

    public DamageAiAnalysisResult() {
    }

    public DamageAiAnalysisResult(
            Long id,
            Long damageId,
            Boolean damaged,
            Integer damageScore,
            String damageType,
            Boolean repairRequired,
            String repairPriority,
            BigDecimal confidenceScore,
            String analysisStatus,
            String rawResult,
            LocalDateTime analyzedAt,
            LocalDateTime createdAt
    ) {
        this.id = id;
        this.damageId = damageId;
        this.damaged = damaged;
        this.damageScore = damageScore;
        this.damageType = damageType;
        this.repairRequired = repairRequired;
        this.repairPriority = repairPriority;
        this.confidenceScore = confidenceScore;
        this.analysisStatus = analysisStatus;
        this.rawResult = rawResult;
        this.analyzedAt = analyzedAt;
        this.createdAt = createdAt;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getDamageId() {
        return damageId;
    }

    public void setDamageId(Long damageId) {
        this.damageId = damageId;
    }

    public Boolean getDamaged() {
        return damaged;
    }

    public void setDamaged(Boolean damaged) {
        this.damaged = damaged;
    }

    public Integer getDamageScore() {
        return damageScore;
    }

    public void setDamageScore(Integer damageScore) {
        this.damageScore = damageScore;
    }

    public String getDamageType() {
        return damageType;
    }

    public void setDamageType(String damageType) {
        this.damageType = damageType;
    }

    public Boolean getRepairRequired() {
        return repairRequired;
    }

    public void setRepairRequired(Boolean repairRequired) {
        this.repairRequired = repairRequired;
    }

    public String getRepairPriority() {
        return repairPriority;
    }

    public void setRepairPriority(String repairPriority) {
        this.repairPriority = repairPriority;
    }

    public BigDecimal getConfidenceScore() {
        return confidenceScore;
    }

    public void setConfidenceScore(BigDecimal confidenceScore) {
        this.confidenceScore = confidenceScore;
    }

    public String getAnalysisStatus() {
        return analysisStatus;
    }

    public void setAnalysisStatus(String analysisStatus) {
        this.analysisStatus = analysisStatus;
    }

    public String getRawResult() {
        return rawResult;
    }

    public void setRawResult(String rawResult) {
        this.rawResult = rawResult;
    }

    public LocalDateTime getAnalyzedAt() {
        return analyzedAt;
    }

    public void setAnalyzedAt(LocalDateTime analyzedAt) {
        this.analyzedAt = analyzedAt;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
