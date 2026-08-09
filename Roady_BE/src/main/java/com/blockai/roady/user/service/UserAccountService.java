package com.blockai.roady.user.service;

import com.blockai.roady.user.domain.UserAccount;
import com.blockai.roady.user.domain.UserRole;

import java.util.List;
import java.util.Optional;

public interface UserAccountService {

    UserAccount create(String username, String rawPassword, String email, String name, UserRole role);

    Optional<UserAccount> findById(Long id);

    Optional<UserAccount> findByUsername(String username);

    List<UserAccount> findAll();

    List<UserAccount> findAll(UserRole role, Boolean active);

    UserAccount updateRole(Long id, UserRole role);

    UserAccount updateActive(Long id, boolean active);

    UserAccount updateAssignedRegion(Long id, String assignedRegionCode);
}
