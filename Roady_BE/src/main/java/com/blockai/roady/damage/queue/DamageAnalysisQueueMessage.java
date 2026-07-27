package com.blockai.roady.damage.queue;

public record DamageAnalysisQueueMessage(
        Long analysisResultId,
        Long damageId
) {
}
