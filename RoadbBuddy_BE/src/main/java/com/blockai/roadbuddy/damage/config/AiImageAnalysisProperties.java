package com.blockai.roadbuddy.damage.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

@ConfigurationProperties(prefix = "roadbuddy.ai.image-analysis")
public class AiImageAnalysisProperties {

    private String endpointUrl;
    private boolean workerEnabled;
    private String queueKey = "roadbuddy:damage:image-analysis:queue";
    private String deadLetterQueueKey = "roadbuddy:damage:image-analysis:dead-letter";
    private int batchSize = 3;
    private Duration requestTimeout = Duration.ofMinutes(3);

    public String getEndpointUrl() {
        return endpointUrl;
    }

    public void setEndpointUrl(String endpointUrl) {
        this.endpointUrl = endpointUrl;
    }

    public boolean isWorkerEnabled() {
        return workerEnabled;
    }

    public void setWorkerEnabled(boolean workerEnabled) {
        this.workerEnabled = workerEnabled;
    }

    public String getQueueKey() {
        return queueKey;
    }

    public void setQueueKey(String queueKey) {
        this.queueKey = queueKey;
    }

    public String getDeadLetterQueueKey() {
        return deadLetterQueueKey;
    }

    public void setDeadLetterQueueKey(String deadLetterQueueKey) {
        this.deadLetterQueueKey = deadLetterQueueKey;
    }

    public int getBatchSize() {
        return batchSize;
    }

    public void setBatchSize(int batchSize) {
        this.batchSize = batchSize;
    }

    public Duration getRequestTimeout() {
        return requestTimeout;
    }

    public void setRequestTimeout(Duration requestTimeout) {
        this.requestTimeout = requestTimeout;
    }
}
