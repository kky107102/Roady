package com.blockai.roady.damage.service;

import com.blockai.roady.damage.domain.DamageAiAnalysisResult;
import com.blockai.roady.damage.domain.DamageAiAnalysisStatus;
import com.blockai.roady.damage.domain.DamageStatus;
import com.blockai.roady.damage.mapper.DamageAiAnalysisResultMapper;
import com.blockai.roady.damage.mapper.DamageMapper;
import com.blockai.roady.damage.queue.DamageAnalysisQueue;
import com.blockai.roady.damage.queue.DamageAnalysisQueueMessage;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
public class DamageAiAnalysisService {

    private final DamageMapper damageMapper;
    private final DamageAiAnalysisResultMapper analysisResultMapper;
    private final DamageAnalysisQueue queue;

    public DamageAiAnalysisService(
            DamageMapper damageMapper,
            DamageAiAnalysisResultMapper analysisResultMapper,
            DamageAnalysisQueue queue
    ) {
        this.damageMapper = damageMapper;
        this.analysisResultMapper = analysisResultMapper;
        this.queue = queue;
    }

    @Transactional
    public DamageAiAnalysisResult createAndEnqueue(Long damageId) {
        if (damageMapper.findSummaryById(damageId) == null) {
            throw new IllegalArgumentException("Damage not found.");
        }

        DamageAiAnalysisResult result = new DamageAiAnalysisResult();
        result.setDamageId(damageId);
        result.setAnalysisStatus(DamageAiAnalysisStatus.QUEUED);
        analysisResultMapper.insert(result);
        updateDamageStatus(damageId, DamageStatus.AI_ANALYZING);

        queue.enqueue(new DamageAnalysisQueueMessage(result.getId(), damageId));

        return getAnalysisResult(result.getId());
    }

    @Transactional
    public void markProcessing(Long analysisResultId) {
        if (analysisResultMapper.markProcessing(analysisResultId) != 1) {
            throw new IllegalArgumentException("Damage AI analysis result not found.");
        }
    }

    @Transactional
    public void markSucceeded(
            Long analysisResultId,
            Long damageId,
            ParsedAiImageAnalysisResult parsedResult,
            String rawResult
    ) {
        int updatedRows = analysisResultMapper.markSucceeded(
                analysisResultId,
                parsedResult.damaged(),
                parsedResult.damageScore(),
                parsedResult.damageType(),
                parsedResult.repairRequired(),
                parsedResult.repairPriority(),
                parsedResult.confidenceScore(),
                rawResult
        );
        if (updatedRows != 1) {
            throw new IllegalArgumentException("Damage AI analysis result not found.");
        }
        updateDamageStatus(damageId, DamageStatus.AI_ANALYZED);
    }

    @Transactional
    public void markFailed(Long analysisResultId, Long damageId, String rawResult) {
        if (analysisResultMapper.markFailed(analysisResultId, rawResult) != 1) {
            throw new IllegalArgumentException("Damage AI analysis result not found.");
        }
        updateDamageStatus(damageId, DamageStatus.COLLECTED);
    }

    @Transactional(readOnly = true)
    public DamageAiAnalysisResult getAnalysisResult(Long analysisResultId) {
        return Optional.ofNullable(analysisResultMapper.findById(analysisResultId))
                .orElseThrow(() -> new IllegalArgumentException("Damage AI analysis result not found."));
    }

    @Transactional(readOnly = true)
    public List<DamageAiAnalysisResult> getAnalysisResultsByDamageId(Long damageId) {
        if (damageMapper.findSummaryById(damageId) == null) {
            throw new IllegalArgumentException("Damage not found.");
        }
        return analysisResultMapper.findByDamageId(damageId);
    }

    private void updateDamageStatus(Long damageId, DamageStatus status) {
        if (damageMapper.updateStatus(damageId, status.name()) != 1) {
            throw new IllegalArgumentException("Damage not found.");
        }
    }
}
