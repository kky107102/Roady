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

    @Test
    void inspectorCanCreateAndReadRobotCommands() throws Exception {
        String adminToken = login("admin", "admin1234");
        String inspectorToken = login("inspector", "inspector1234");
        Long inspectorId = userId("inspector");
        Long robotId = createRobot(adminToken, inspectorId, "Command Robot", uniqueSerialNumber());

        mockMvc.perform(post("/api/robots/{robotId}/commands", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(inspectorToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "commandType": "START_PATROL"
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.robotId").value(robotId))
                .andExpect(jsonPath("$.requestedBy").value(inspectorId))
                .andExpect(jsonPath("$.commandType").value("START_PATROL"))
                .andExpect(jsonPath("$.commandStatus").value("PENDING"))
                .andExpect(jsonPath("$.requestedAt").exists());

        mockMvc.perform(get("/api/robots/{robotId}/commands", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(inspectorToken)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].robotId").value(robotId))
                .andExpect(jsonPath("$[0].commandType").value("START_PATROL"));
    }

    @Test
    void viewerCannotCreateOrReadRobotCommands() throws Exception {
        String adminToken = login("admin", "admin1234");
        String viewerToken = login("viewer", "viewer1234");
        Long inspectorId = userId("inspector");
        Long robotId = createRobot(adminToken, inspectorId, "Forbidden Command Robot", uniqueSerialNumber());

        mockMvc.perform(post("/api/robots/{robotId}/commands", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "commandType": "EMERGENCY_STOP"
                                }
                                """))
                .andExpect(status().isForbidden());

        mockMvc.perform(get("/api/robots/{robotId}/commands", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken)))
                .andExpect(status().isForbidden());
    }

    @Test
    void inspectorCanCreateAndReadRobotStatusLogs() throws Exception {
        String adminToken = login("admin", "admin1234");
        String inspectorToken = login("inspector", "inspector1234");
        String viewerToken = login("viewer", "viewer1234");
        Long inspectorId = userId("inspector");
        Long robotId = createRobot(adminToken, inspectorId, "Status Robot", uniqueSerialNumber());

        mockMvc.perform(post("/api/robots/{robotId}/status-logs", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(inspectorToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "latitude": 37.5665,
                                  "longitude": 126.978,
                                  "batteryLevel": 72,
                                  "operationStatus": "INSPECTING",
                                  "connectionStatus": "CONNECTED",
                                  "errorCode": null,
                                  "errorMessage": null,
                                  "recordedAt": "2026-07-22T14:30:00"
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.robotId").value(robotId))
                .andExpect(jsonPath("$.batteryLevel").value(72))
                .andExpect(jsonPath("$.operationStatus").value("INSPECTING"))
                .andExpect(jsonPath("$.connectionStatus").value("CONNECTED"))
                .andExpect(jsonPath("$.recordedAt").value("2026-07-22T14:30:00"));

        mockMvc.perform(get("/api/robots/{robotId}/status-logs/latest", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.robotId").value(robotId))
                .andExpect(jsonPath("$.operationStatus").value("INSPECTING"));

        mockMvc.perform(get("/api/robots/{robotId}/status-logs", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(inspectorToken)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].robotId").value(robotId))
                .andExpect(jsonPath("$[0].operationStatus").value("INSPECTING"));

        mockMvc.perform(get("/api/robots/{robotId}", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("INSPECTING"))
                .andExpect(jsonPath("$.latestStatus.robotId").doesNotExist())
                .andExpect(jsonPath("$.latestStatus.batteryLevel").value(72))
                .andExpect(jsonPath("$.latestStatus.operationStatus").value("INSPECTING"));
    }

    @Test
    void viewerCannotCreateOrReadRobotStatusLogList() throws Exception {
        String adminToken = login("admin", "admin1234");
        String viewerToken = login("viewer", "viewer1234");
        Long inspectorId = userId("inspector");
        Long robotId = createRobot(adminToken, inspectorId, "Forbidden Status Robot", uniqueSerialNumber());

        mockMvc.perform(post("/api/robots/{robotId}/status-logs", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "latitude": 37.5665,
                                  "longitude": 126.978,
                                  "batteryLevel": 72,
                                  "operationStatus": "INSPECTING",
                                  "connectionStatus": "CONNECTED"
                                }
                                """))
                .andExpect(status().isForbidden());

        mockMvc.perform(get("/api/robots/{robotId}/status-logs", robotId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken)))
                .andExpect(status().isForbidden());
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
