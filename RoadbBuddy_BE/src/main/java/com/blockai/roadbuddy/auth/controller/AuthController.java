package com.blockai.roadbuddy.auth.controller;

import com.blockai.roadbuddy.auth.dto.LoginRequest;
import com.blockai.roadbuddy.auth.dto.LogoutRequest;
import com.blockai.roadbuddy.auth.dto.MeResponse;
import com.blockai.roadbuddy.auth.dto.RefreshTokenRequest;
import com.blockai.roadbuddy.auth.dto.SignupRequest;
import com.blockai.roadbuddy.auth.dto.TokenResponse;
import com.blockai.roadbuddy.auth.service.AuthService;
import com.blockai.roadbuddy.security.AuthenticatedUser;
import com.blockai.roadbuddy.user.dto.UserResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
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

    @PostMapping("/signup")
    @ResponseStatus(HttpStatus.CREATED)
    public UserResponse signup(@Valid @RequestBody SignupRequest request) {
        return UserResponse.from(authService.signup(
                request.username(),
                request.password(),
                request.email(),
                request.name()
        ));
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
