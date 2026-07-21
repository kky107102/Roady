package com.blockai.roadbuddy.auth.controller;

import com.blockai.roadbuddy.auth.dto.LoginRequest;
import com.blockai.roadbuddy.auth.dto.LogoutRequest;
import com.blockai.roadbuddy.auth.dto.MeResponse;
import com.blockai.roadbuddy.auth.dto.RefreshTokenRequest;
import com.blockai.roadbuddy.auth.dto.TokenResponse;
import com.blockai.roadbuddy.auth.service.AuthService;
import com.blockai.roadbuddy.security.AuthenticatedUser;
import jakarta.validation.Valid;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public TokenResponse login(@Valid @RequestBody LoginRequest request) {
        return authService.login(request.username(), request.password());
    }

    @PostMapping("/refresh")
    public TokenResponse refresh(@Valid @RequestBody RefreshTokenRequest request) {
        return authService.refresh(request.refreshToken());
    }

    @PostMapping("/logout")
    public void logout(@Valid @RequestBody LogoutRequest request) {
        authService.logout(request.refreshToken());
    }

    @GetMapping("/me")
    public MeResponse me(@AuthenticationPrincipal AuthenticatedUser user) {
        return MeResponse.from(user);
    }
}
