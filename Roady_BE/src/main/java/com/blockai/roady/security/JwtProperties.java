package com.blockai.roady.security;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "roady.jwt")
public record JwtProperties(
        String secret,
        long accessTokenValidityMinutes,
        long refreshTokenValidityDays
) {

    private static final String DEFAULT_SECRET =
            "roady-local-development-secret-key-change-before-production";

    public JwtProperties {
        if (secret == null || secret.isBlank()) {
            secret = DEFAULT_SECRET;
        }
        if (accessTokenValidityMinutes <= 0) {
            accessTokenValidityMinutes = 30;
        }
        if (refreshTokenValidityDays <= 0) {
            refreshTokenValidityDays = 14;
        }
    }
}
