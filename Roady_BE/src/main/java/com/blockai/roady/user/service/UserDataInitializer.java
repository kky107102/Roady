package com.blockai.roady.user.service;

import com.blockai.roady.user.domain.UserRole;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

@Component
@Profile("!inmemory")
@ConditionalOnProperty(prefix = "roady.default-users", name = "enabled", havingValue = "true", matchIfMissing = true)
public class UserDataInitializer implements ApplicationRunner {

    private final UserAccountService userAccountService;

    public UserDataInitializer(UserAccountService userAccountService) {
        this.userAccountService = userAccountService;
    }

    @Override
    public void run(ApplicationArguments args) {
        seedUser("admin", "roady0810", "admin@roady.local", "관리자", UserRole.ADMIN);
        seedUser("inspector", "roady0810", "inspector@roady.local", "점검 담당자", UserRole.INSPECTOR);
        seedUser("repairer", "roady0810", "repairer@roady.local", "보수 담당자", UserRole.REPAIRER);
        seedUser("viewer", "roady0810", "viewer@roady.local", "조회 사용자", UserRole.VIEWER);
    }

    private void seedUser(String username, String password, String email, String name, UserRole role) {
        if (userAccountService.findByUsername(username).isPresent()) {
            return;
        }
        userAccountService.create(username, password, email, name, role);
    }
}
