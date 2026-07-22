package com.blockai.roadbuddy.damage.service;

import com.blockai.roadbuddy.damage.config.AiImageAnalysisProperties;
import com.blockai.roadbuddy.damage.domain.DamageAiAnalysisResult;
import com.blockai.roadbuddy.damage.domain.DamageAiAnalysisStatus;
import com.blockai.roadbuddy.damage.mapper.DamageAiAnalysisResultMapper;
import com.blockai.roadbuddy.damage.mapper.DamageMapper;
import com.blockai.roadbuddy.damage.queue.DamageAnalysisQueue;
import com.blockai.roadbuddy.damage.queue.DamageAnalysisQueueMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(prefix = "roadbuddy.ai.image-analysis", name = "worker-enabled", havingValue = "true")
public class DamageAnalysisWorker {

    private static final Logger log = LoggerFactory.getLogger(DamageAnalysisWorker.class);

    private final DamageAnalysisQueue queue;
    private final DamageAiAnalysisResultMapper analysisResultMapper;
    private final DamageMapper damageMapper;
    private final AiImageAnalysisClient aiClient;
    private final AiImageAnalysisResultParser resultParser;
    private final AiImageAnalysisProperties properties;

    public DamageAnalysisWorker(
            DamageAnalysisQueue queue,
            DamageAiAnalysisResultMapper analysisResultMapper,
            DamageMapper damageMapper,
            AiImageAnalysisClient aiClient,
            AiImageAnalysisResultParser resultParser,
            AiImageAnalysisProperties properties
    ) {
        this.queue = queue;
        this.analysisResultMapper = analysisResultMapper;
        this.damageMapper = damageMapper;
        this.aiClient = aiClient;
        this.resultParser = resultParser;
        this.properties = properties;
    }

    @Scheduled(fixedDelayString = "${roadbuddy.ai.image-analysis.poll-delay-ms:1000}")
    public void consumeQueuedJobs() {
        int batchSize = Math.max(1, properties.getBatchSize());
        for (int i = 0; i < batchSize; i++) {
            DamageAnalysisQueueMessage message = queue.poll();
            if (message == null) {
                return;
            }
            process(message);
        }
    }

    private void process(DamageAnalysisQueueMessage message) {
        DamageAiAnalysisResult analysisResult = analysisResultMapper.findById(message.analysisResultId());
        if (analysisResult == null) {
            log.warn("Skipping missing damage AI analysis result. analysisResultId={}", message.analysisResultId());
            queue.deadLetter(message);
            return;
        }
        if (DamageAiAnalysisStatus.SUCCESS.equals(analysisResult.getAnalysisStatus())) {
            return;
        }

        try {
            analysisResultMapper.markProcessing(analysisResult.getId());
            var damage = damageMapper.findSummaryById(message.damageId());
            if (damage == null) {
                throw new IllegalArgumentException("Damage not found.");
            }
            var images = damageMapper.findImagesByDamageId(message.damageId());
            if (images.isEmpty()) {
                throw new IllegalArgumentException("Damage images not found.");
            }

            String rawResult = aiClient.analyze(damage, images);
            ParsedAiImageAnalysisResult parsedResult = resultParser.parse(rawResult);
            analysisResultMapper.markSucceeded(
                    analysisResult.getId(),
                    parsedResult.damaged(),
                    parsedResult.damageScore(),
                    parsedResult.repairRequired(),
                    parsedResult.repairPriority(),
                    parsedResult.confidenceScore(),
                    rawResult
            );
        } catch (RuntimeException ex) {
            log.warn(
                    "Damage AI analysis failed. analysisResultId={}, damageId={}",
                    message.analysisResultId(),
                    message.damageId(),
                    ex
            );
            analysisResultMapper.markFailed(analysisResult.getId(), ex.getMessage());
            queue.deadLetter(message);
        }
    }
}
