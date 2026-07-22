package com.blockai.roadbuddy.auth.dto;

public record TokenResponse(
        String tokenType,
        String accessToken,
        String refreshToken,
        long expiresInSeconds
) {

    public static TokenResponse bearer(String accessToken, String refreshToken, long expiresInSeconds) {
        return new TokenResponse("Bearer", accessToken, refreshToken, expiresInSeconds);
    }
}
