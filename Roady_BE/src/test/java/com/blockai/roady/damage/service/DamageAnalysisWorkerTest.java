package com.blockai.roady.damage.service;

import com.blockai.roady.damage.config.AiImageAnalysisProperties;
import com.blockai.roady.damage.domain.DamageAiAnalysisResult;
import com.blockai.roady.damage.domain.DamageAiAnalysisStatus;
import com.blockai.roady.damage.domain.DamageImage;
import com.blockai.roady.damage.domain.DamageSummary;
import com.blockai.roady.damage.mapper.DamageAiAnalysisResultMapper;
import com.blockai.roady.damage.mapper.DamageMapper;
import com.blockai.roady.damage.queue.DamageAnalysisQueue;
import com.blockai.roady.damage.queue.DamageAnalysisQueueMessage;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class DamageAnalysisWorkerTest {

    @Mock
    private DamageAnalysisQueue queue;

    @Mock
    private DamageAiAnalysisResultMapper analysisResultMapper;

    @Mock
    private DamageMapper damageMapper;

    @Mock
    private AiImageAnalysisClient aiClient;

    @Mock
    private AiImageAnalysisResultParser resultParser;

    private DamageAnalysisWorker worker;

    @BeforeEach
    void setUp() {
        AiImageAnalysisProperties properties = new AiImageAnalysisProperties();
        properties.setBatchSize(1);
        worker = new DamageAnalysisWorker(
                queue,
                analysisResultMapper,
                damageMapper,
                aiClient,
                resultParser,
                properties
        );
    }

    @Test
    void consumeQueuedJobsStoresAiResponseIntoAnalysisResult() {
        DamageAnalysisQueueMessage message = new DamageAnalysisQueueMessage(10L, 1L);
        String rawResult = """
                {"damaged":true,"damageScore":82,"repairRequired":true,"repairPriority":"HIGH","confidenceScore":0.91}
                """;
        ParsedAiImageAnalysisResult parsedResult = new ParsedAiImageAnalysisResult(
                true,
                82,
                true,
                "HIGH",
                BigDecimal.valueOf(0.91)
        );

        when(queue.poll()).thenReturn(message);
        when(analysisResultMapper.findById(10L)).thenReturn(result(10L, 1L, DamageAiAnalysisStatus.QUEUED));
        when(damageMapper.findSummaryById(1L)).thenReturn(summary(1L));
        when(damageMapper.findImagesByDamageId(1L)).thenReturn(List.of(image(1L, 1L)));
        when(aiClient.analyze(any(DamageSummary.class), any())).thenReturn(rawResult);
        when(resultParser.parse(rawResult)).thenReturn(parsedResult);

        worker.consumeQueuedJobs();

        verify(analysisResultMapper).markProcessing(10L);
        verify(analysisResultMapper).markSucceeded(
                10L,
                true,
                82,
                true,
                "HIGH",
                BigDecimal.valueOf(0.91),
                rawResult
        );
        verify(queue, never()).deadLetter(any(DamageAnalysisQueueMessage.class));
    }

    @Test
    void consumeQueuedJobsMarksFailedAndDeadLettersWhenAiCallFails() {
        DamageAnalysisQueueMessage message = new DamageAnalysisQueueMessage(10L, 1L);
        when(queue.poll()).thenReturn(message);
        when(analysisResultMapper.findById(10L)).thenReturn(result(10L, 1L, DamageAiAnalysisStatus.QUEUED));
        when(damageMapper.findSummaryById(1L)).thenReturn(summary(1L));
        when(damageMapper.findImagesByDamageId(1L)).thenReturn(List.of(image(1L, 1L)));
        when(aiClient.analyze(any(DamageSummary.class), any()))
                .thenThrow(new IllegalStateException("AI server unavailable"));

        worker.consumeQueuedJobs();

        verify(analysisResultMapper).markProcessing(10L);
        verify(analysisResultMapper).markFailed(10L, "AI server unavailable");
        verify(queue).deadLetter(eq(message));
    }

    @Test
    void consumeQueuedJobsSkipsAlreadySucceededResult() {
        DamageAnalysisQueueMessage message = new DamageAnalysisQueueMessage(10L, 1L);
        when(queue.poll()).thenReturn(message);
        when(analysisResultMapper.findById(10L)).thenReturn(result(10L, 1L, DamageAiAnalysisStatus.SUCCESS));

        worker.consumeQueuedJobs();

        verify(analysisResultMapper, never()).markProcessing(10L);
        verify(aiClient, never()).analyze(any(), any());
    }

    private DamageAiAnalysisResult result(Long id, Long damageId, String status) {
        DamageAiAnalysisResult result = new DamageAiAnalysisResult();
        result.setId(id);
        result.setDamageId(damageId);
        result.setAnalysisStatus(status);
        return result;
    }

    private DamageSummary summary(Long damageId) {
        LocalDateTime now = LocalDateTime.of(2026, 7, 27, 10, 0);
        return new DamageSummary(
                damageId,
                null,
                2L,
                null,
                "road damage",
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                now,
                "COLLECTED",
                1L,
                now,
                now
        );
    }

    private DamageImage image(Long imageId, Long damageId) {
        LocalDateTime now = LocalDateTime.of(2026, 7, 27, 10, 0);
        return new DamageImage(
                imageId,
                damageId,
                1,
                "damage.jpg",
                "image/jpeg",
                3L,
                new byte[]{1, 2, 3},
                now
        );
    }
}
