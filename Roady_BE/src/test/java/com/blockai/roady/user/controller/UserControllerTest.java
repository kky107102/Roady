package com.blockai.roady.user.controller;

import com.blockai.roady.common.exception.GlobalExceptionHandler;
import com.blockai.roady.user.domain.UserAccount;
import com.blockai.roady.user.domain.UserRole;
import com.blockai.roady.user.service.UserAccountService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.time.LocalDateTime;
import java.util.List;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class UserControllerTest {

    private UserAccountService userAccountService;
    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        userAccountService = mock(UserAccountService.class);
        UserController controller = new UserController(userAccountService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller)
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    void updateAssignedRegionReturnsUpdatedUser() throws Exception {
        when(userAccountService.updateAssignedRegion(5L, "11680"))
                .thenReturn(new UserAccount(
                        5L,
                        "inspector",
                        "hash",
                        "inspector@roady.local",
                        "Inspector",
                        "11680",
                        UserRole.INSPECTOR,
                        true,
                        LocalDateTime.of(2026, 7, 30, 10, 0)
                ));

        mockMvc.perform(patch("/api/users/5/assigned-region")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "assignedRegionCode": "11680"
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(5))
                .andExpect(jsonPath("$.username").value("inspector"))
                .andExpect(jsonPath("$.assignedRegionCode").value("11680"));
    }

    @Test
    void getUsersPassesRepairerAndActiveFilters() throws Exception {
        when(userAccountService.findAll(UserRole.REPAIRER, true))
                .thenReturn(List.of(new UserAccount(
                        9L,
                        "repairer",
                        "hash",
                        "repairer@roady.local",
                        "Repairer",
                        null,
                        UserRole.REPAIRER,
                        true,
                        LocalDateTime.of(2026, 8, 4, 10, 0)
                )));

        mockMvc.perform(get("/api/users")
                        .param("role", "REPAIRER")
                        .param("active", "true"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(9))
                .andExpect(jsonPath("$[0].name").value("Repairer"))
                .andExpect(jsonPath("$[0].role").value("REPAIRER"))
                .andExpect(jsonPath("$[0].active").value(true));

        verify(userAccountService).findAll(UserRole.REPAIRER, true);
    }
}
