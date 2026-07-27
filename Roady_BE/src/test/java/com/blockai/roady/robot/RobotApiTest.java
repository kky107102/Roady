package com.blockai.roady.robot;

import com.blockai.roady.user.service.UserAccountService;
import com.jayway.jsonpath.JsonPath;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.hamcrest.Matchers.nullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class RobotApiTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserAccountService userAccountService;

    @Test
    void adminCanCreateReadAndUpdateRobot() throws Exception {
        String adminToken = login("admin", "admin1234");
        Long inspectorId = userId("inspector");
        String serialNumber = uniqueSerialNumber();

        Long robotId = createRobot(adminToken, inspectorId, "Inspection Robot", serialNumber);

        mockMvc.perform(get("/api/robots/{robotId}", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(adminToken)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(robotId))
                .andExpect(jsonPath("$.userId").value(inspectorId))
                .andExpect(jsonPath("$.name").value("Inspection Robot"))
                .andExpect(jsonPath("$.serialNumber").value(serialNumber))
                .andExpect(jsonPath("$.status").value("STANDBY"))
                .andExpect(jsonPath("$.active").value(true))
                .andExpect(jsonPath("$.latestStatus").value(nullValue()));

        mockMvc.perform(patch("/api/robots/{robotId}", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(adminToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "Updated Robot",
                                  "active": false
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Updated Robot"))
                .andExpect(jsonPath("$.active").value(false));

        mockMvc.perform(patch("/api/robots/{robotId}/active", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(adminToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "active": true
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.active").value(true));
    }

    @Test
    void viewerCanReadRobotsButCannotCreateRobot() throws Exception {
        String adminToken = login("admin", "admin1234");
        String viewerToken = login("viewer", "viewer1234");
        Long inspectorId = userId("inspector");
        Long robotId = createRobot(adminToken, inspectorId, "Viewer Read Robot", uniqueSerialNumber());

        mockMvc.perform(get("/api/robots")
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken)))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/robots/{robotId}", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(robotId));

        mockMvc.perform(post("/api/robots")
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(createRobotRequest(inspectorId, "Forbidden Robot", uniqueSerialNumber())))
                .andExpect(status().isForbidden());
    }

    @Test
    void createRobotRejectsDuplicateSerialNumber() throws Exception {
        String adminToken = login("admin", "admin1234");
        Long inspectorId = userId("inspector");
        String serialNumber = uniqueSerialNumber();

        createRobot(adminToken, inspectorId, "Original Robot", serialNumber);

        mockMvc.perform(post("/api/robots")
                        .header(HttpHeaders.AUTHORIZATION, bearer(adminToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(createRobotRequest(inspectorId, "Duplicate Robot", serialNumber)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.message").value("Already used robot serial number."));
    }

    private Long createRobot(String accessToken, Long userId, String name, String serialNumber) throws Exception {
        MvcResult result = mockMvc.perform(post("/api/robots")
                        .header(HttpHeaders.AUTHORIZATION, bearer(accessToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(createRobotRequest(userId, name, serialNumber)))
                .andExpect(status().isCreated())
                .andReturn();

        Number id = JsonPath.read(result.getResponse().getContentAsString(), "$.id");
        return id.longValue();
    }

    private String createRobotRequest(Long userId, String name, String serialNumber) {
        return """
                {
                  "userId": %d,
                  "name": "%s",
                  "serialNumber": "%s"
                }
                """.formatted(userId, name, serialNumber);
    }

    private Long userId(String username) {
        return userAccountService.findByUsername(username)
                .orElseThrow()
                .id();
    }

    private String login(String username, String password) throws Exception {
        MvcResult result = mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "username": "%s",
                                  "password": "%s"
                                }
                                """.formatted(username, password)))
                .andExpect(status().isOk())
                .andReturn();

        return JsonPath.read(result.getResponse().getContentAsString(), "$.accessToken");
    }

    private String bearer(String accessToken) {
        return "Bearer " + accessToken;
    }

    private String uniqueSerialNumber() {
        return "RB-" + System.nanoTime();
    }
}
