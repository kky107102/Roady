package com.blockai.roady.damage.service;

import com.blockai.roady.damage.domain.DamageAiAnalysisResult;
import com.blockai.roady.damage.domain.DamageAiAnalysisStatus;
import com.blockai.roady.damage.domain.DamageSummary;
import com.blockai.roady.damage.mapper.DamageAiAnalysisResultMapper;
import com.blockai.roady.damage.mapper.DamageMapper;
import com.blockai.roady.damage.queue.DamageAnalysisQueue;
import com.blockai.roady.damage.queue.DamageAnalysisQueueMessage;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class DamageAiAnalysisServiceTest {

    @Mock
    private DamageMapper damageMapper;

    @Mock
    private DamageAiAnalysisResultMapper analysisResultMapper;

    @Mock
    private DamageAnalysisQueue queue;

    @InjectMocks
    private DamageAiAnalysisService service;

    @Test
    void createAndEnqueueCreatesQueuedResultAndPushesQueueMessage() {
        when(damageMapper.findSummaryById(1L)).thenReturn(summary(1L));
        doAnswer(invocation -> {
            DamageAiAnalysisResult result = invocation.getArgument(0);
            result.setId(10L);
            return 1;
        }).when(analysisResultMapper).insert(any(DamageAiAnalysisResult.class));
        DamageAiAnalysisResult savedResult = result(10L, 1L, DamageAiAnalysisStatus.QUEUED);
        when(analysisResultMapper.findById(10L)).thenReturn(savedResult);
        when(damageMapper.updateStatus(1L, "AI_ANALYZING")).thenReturn(1);

        DamageAiAnalysisResult result = service.createAndEnqueue(1L);

        ArgumentCaptor<DamageAiAnalysisResult> resultCaptor = ArgumentCaptor.forClass(DamageAiAnalysisResult.class);
        ArgumentCaptor<DamageAnalysisQueueMessage> messageCaptor =
                ArgumentCaptor.forClass(DamageAnalysisQueueMessage.class);
        verify(analysisResultMapper).insert(resultCaptor.capture());
        verify(damageMapper).updateStatus(1L, "AI_ANALYZING");
        verify(queue).enqueue(messageCaptor.capture());

        assertThat(resultCaptor.getValue().getDamageId()).isEqualTo(1L);
        assertThat(resultCaptor.getValue().getAnalysisStatus()).isEqualTo(DamageAiAnalysisStatus.QUEUED);
        assertThat(messageCaptor.getValue().analysisResultId()).isEqualTo(10L);
        assertThat(messageCaptor.getValue().damageId()).isEqualTo(1L);
        assertThat(result).isSameAs(savedResult);
    }

    @Test
    void createAndEnqueueRejectsMissingDamage() {
        when(damageMapper.findSummaryById(404L)).thenReturn(null);

        assertThatThrownBy(() -> service.createAndEnqueue(404L))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Damage not found.");

        verify(analysisResultMapper, never()).insert(any(DamageAiAnalysisResult.class));
        verify(queue, never()).enqueue(any(DamageAnalysisQueueMessage.class));
    }

    @Test
    void markSucceededStoresResultAndMovesDamageToAiAnalyzed() {
        ParsedAiImageAnalysisResult parsedResult = new ParsedAiImageAnalysisResult(
                true,
                82,
                "CRACK",
                true,
                "HIGH",
                java.math.BigDecimal.valueOf(0.91)
        );
        when(analysisResultMapper.markSucceeded(
                10L,
                true,
                82,
                "CRACK",
                true,
                "HIGH",
                java.math.BigDecimal.valueOf(0.91),
                "raw-result"
        )).thenReturn(1);
        when(damageMapper.updateStatus(1L, "AI_ANALYZED")).thenReturn(1);

        service.markSucceeded(10L, 1L, parsedResult, "raw-result");

        verify(damageMapper).updateStatus(1L, "AI_ANALYZED");
    }

    @Test
    void markFailedStoresFailureAndReturnsDamageToCollected() {
        when(analysisResultMapper.markFailed(10L, "AI server unavailable")).thenReturn(1);
        when(damageMapper.updateStatus(1L, "COLLECTED")).thenReturn(1);

        service.markFailed(10L, 1L, "AI server unavailable");

        verify(damageMapper).updateStatus(1L, "COLLECTED");
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
                null,
                null,
                null,
                1L,
                now,
                now
        );
    }

    private DamageAiAnalysisResult result(Long id, Long damageId, String status) {
        DamageAiAnalysisResult result = new DamageAiAnalysisResult();
        result.setId(id);
        result.setDamageId(damageId);
        result.setAnalysisStatus(status);
        return result;
    }
}
