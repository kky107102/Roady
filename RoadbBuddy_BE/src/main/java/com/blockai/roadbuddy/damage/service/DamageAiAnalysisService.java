package com.blockai.roadbuddy.damage.service;

import com.blockai.roadbuddy.damage.domain.DamageAiAnalysisResult;
import com.blockai.roadbuddy.damage.domain.DamageAiAnalysisStatus;
import com.blockai.roadbuddy.damage.mapper.DamageAiAnalysisResultMapper;
import com.blockai.roadbuddy.damage.mapper.DamageMapper;
import com.blockai.roadbuddy.damage.queue.DamageAnalysisQueue;
import com.blockai.roadbuddy.damage.queue.DamageAnalysisQueueMessage;
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

        queue.enqueue(new DamageAnalysisQueueMessage(result.getId(), damageId));

        return getAnalysisResult(result.getId());
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
}
