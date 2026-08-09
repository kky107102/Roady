package com.blockai.roady.user.controller;

import com.blockai.roady.user.domain.UserAccount;
import com.blockai.roady.user.domain.UserRole;
import com.blockai.roady.user.dto.CreateUserRequest;
import com.blockai.roady.user.dto.UpdateUserActiveRequest;
import com.blockai.roady.user.dto.UpdateUserAssignedRegionRequest;
import com.blockai.roady.user.dto.UpdateUserRoleRequest;
import com.blockai.roady.user.dto.UserResponse;
import com.blockai.roady.user.service.UserAccountService;
import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserAccountService userAccountService;

    public UserController(UserAccountService userAccountService) {
        this.userAccountService = userAccountService;
    }

    @GetMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public List<UserResponse> getUsers(
            @RequestParam(required = false) UserRole role,
            @RequestParam(required = false) Boolean active
    ) {
        return userAccountService.findAll(role, active).stream()
                .map(UserResponse::from)
                .toList();
    }

    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public UserResponse createUser(@Valid @RequestBody CreateUserRequest request) {
        UserAccount user = userAccountService.create(
                request.username(),
                request.password(),
                request.email(),
                request.name(),
                request.role()
        );
        return UserResponse.from(user);
    }

    @PatchMapping("/{userId}/role")
    @PreAuthorize("hasRole('ADMIN')")
    public UserResponse updateRole(
            @PathVariable Long userId,
            @Valid @RequestBody UpdateUserRoleRequest request
    ) {
        return UserResponse.from(userAccountService.updateRole(userId, request.role()));
    }

    @PatchMapping("/{userId}/active")
    @PreAuthorize("hasRole('ADMIN')")
    public UserResponse updateActive(
            @PathVariable Long userId,
            @Valid @RequestBody UpdateUserActiveRequest request
    ) {
        return UserResponse.from(userAccountService.updateActive(userId, request.active()));
    }

    @PatchMapping("/{userId}/assigned-region")
    @PreAuthorize("hasRole('ADMIN')")
    public UserResponse updateAssignedRegion(
            @PathVariable Long userId,
            @Valid @RequestBody UpdateUserAssignedRegionRequest request
    ) {
        return UserResponse.from(userAccountService.updateAssignedRegion(
                userId,
                request.assignedRegionCode()
        ));
    }
}
