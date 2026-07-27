package com.blockai.roadbuddy.damage.queue;

public record DamageAnalysisQueueMessage(
        Long analysisResultId,
        Long damageId
) {
}
