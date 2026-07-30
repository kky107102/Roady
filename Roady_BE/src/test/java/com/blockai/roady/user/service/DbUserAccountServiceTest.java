package com.blockai.roady.user.service;

import com.blockai.roady.user.domain.UserAccount;
import com.blockai.roady.user.domain.UserRole;
import com.blockai.roady.user.mapper.UserAccountMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class DbUserAccountServiceTest {

    @Mock
    private UserAccountMapper userAccountMapper;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Test
    void updateAssignedRegionStoresTrimmedRegionCode() {
        DbUserAccountService service = new DbUserAccountService(userAccountMapper, passwordEncoder);
        UserAccount updatedUser = new UserAccount(
                5L,
                "inspector",
                "hash",
                "inspector@roady.local",
                "Inspector",
                "11680",
                UserRole.INSPECTOR,
                true,
                LocalDateTime.of(2026, 7, 30, 10, 0)
        );

        when(userAccountMapper.updateAssignedRegion(5L, "11680")).thenReturn(1);
        when(userAccountMapper.findById(5L)).thenReturn(updatedUser);

        UserAccount result = service.updateAssignedRegion(5L, " 11680 ");

        assertThat(result.assignedRegionCode()).isEqualTo("11680");
    }

    @Test
    void updateAssignedRegionClearsRegionCodeWhenBlank() {
        DbUserAccountService service = new DbUserAccountService(userAccountMapper, passwordEncoder);
        UserAccount updatedUser = new UserAccount(
                5L,
                "inspector",
                "hash",
                "inspector@roady.local",
                "Inspector",
                null,
                UserRole.INSPECTOR,
                true,
                LocalDateTime.of(2026, 7, 30, 10, 0)
        );

        when(userAccountMapper.updateAssignedRegion(5L, null)).thenReturn(1);
        when(userAccountMapper.findById(5L)).thenReturn(updatedUser);

        UserAccount result = service.updateAssignedRegion(5L, " ");

        assertThat(result.assignedRegionCode()).isNull();
    }
}
