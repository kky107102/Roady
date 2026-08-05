package com.blockai.roady.robot.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

@ConfigurationProperties(prefix = "roady.robot-location")
public class RobotLocationProperties {

    private String redisKeyPattern = "roady:robots:{robotId}:location";
    private Duration ttl = Duration.ofMinutes(5);
    private Duration rdbPersistenceInterval = Duration.ofMinutes(1);

    public String getRedisKeyPattern() {
        return redisKeyPattern;
    }

    public void setRedisKeyPattern(String redisKeyPattern) {
        this.redisKeyPattern = redisKeyPattern;
    }

    public String redisKey(Long robotId) {
        return redisKeyPattern.replace("{robotId}", String.valueOf(robotId));
    }

    public Duration getTtl() {
        return ttl;
    }

    public void setTtl(Duration ttl) {
        this.ttl = ttl;
    }

    public Duration getRdbPersistenceInterval() {
        return rdbPersistenceInterval;
    }

    public void setRdbPersistenceInterval(Duration rdbPersistenceInterval) {
        this.rdbPersistenceInterval = rdbPersistenceInterval;
    }
}
