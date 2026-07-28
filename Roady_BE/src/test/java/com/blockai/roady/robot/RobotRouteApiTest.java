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

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class RobotRouteApiTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserAccountService userAccountService;

    @Test
    void inspectorCanCreateReadUpdateAndDeleteRobotRoute() throws Exception {
        String adminToken = login("admin", "admin1234");
        String inspectorToken = login("inspector", "inspector1234");
        String viewerToken = login("viewer", "viewer1234");
        Long inspectorId = userId("inspector");
        Long robotId = createRobot(adminToken, inspectorId, "Route Robot");

        Long routeId = createRoute(inspectorToken, robotId, "서초구 보행로 1구역");

        mockMvc.perform(get("/api/robot-routes")
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken))
                        .param("robotId", robotId.toString())
                        .param("routeStatus", "CREATED"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(routeId))
                .andExpect(jsonPath("$[0].robotId").value(robotId))
                .andExpect(jsonPath("$[0].routeStatus").value("CREATED"));

        mockMvc.perform(get("/api/robot-routes/{routeId}", routeId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(routeId))
                .andExpect(jsonPath("$.createdBy").value(inspectorId))
                .andExpect(jsonPath("$.points.length()").value(2))
                .andExpect(jsonPath("$.points[0].pointType").value("START"))
                .andExpect(jsonPath("$.points[1].pointType").value("DESTINATION"));

        mockMvc.perform(put("/api/robot-routes/{routeId}", routeId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(inspectorToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "name": "서초구 보행로 1구역 수정",
                                  "routeStatus": "CREATED",
                                  "points": [
                                    {
                                      "pointOrder": 1,
                                      "latitude": 37.5665,
                                      "longitude": 126.978,
                                      "pointType": "START"
                                    },
                                    {
                                      "pointOrder": 2,
                                      "latitude": 37.5658,
                                      "longitude": 126.9786,
                                      "pointType": "WAYPOINT"
                                    },
                                    {
                                      "pointOrder": 3,
                                      "latitude": 37.5651,
                                      "longitude": 126.9792,
                                      "pointType": "DESTINATION"
                                    }
                                  ]
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("서초구 보행로 1구역 수정"))
                .andExpect(jsonPath("$.points.length()").value(3))
                .andExpect(jsonPath("$.points[1].pointType").value("WAYPOINT"));

        mockMvc.perform(delete("/api/robot-routes/{routeId}", routeId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(inspectorToken)))
                .andExpect(status().isNoContent());

        mockMvc.perform(get("/api/robot-routes/{routeId}", routeId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void routeRejectsInvalidPointComposition() throws Exception {
        String adminToken = login("admin", "admin1234");
        String inspectorToken = login("inspector", "inspector1234");
        Long inspectorId = userId("inspector");
        Long robotId = createRobot(adminToken, inspectorId, "Invalid Route Robot");

        mockMvc.perform(post("/api/robot-routes")
                        .header(HttpHeaders.AUTHORIZATION, bearer(inspectorToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "robotId": %d,
                                  "name": "잘못된 경로",
                                  "points": [
                                    {
                                      "pointOrder": 1,
                                      "latitude": 37.5665,
                                      "longitude": 126.978,
                                      "pointType": "START"
                                    },
                                    {
                                      "pointOrder": 1,
                                      "latitude": 37.5651,
                                      "longitude": 126.9792,
                                      "pointType": "DESTINATION"
                                    }
                                  ]
                                }
                                """.formatted(robotId)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value("Route point order must be unique."));
    }

    @Test
    void viewerCannotCreateUpdateOrDeleteRobotRoute() throws Exception {
        String adminToken = login("admin", "admin1234");
        String inspectorToken = login("inspector", "inspector1234");
        String viewerToken = login("viewer", "viewer1234");
        Long inspectorId = userId("inspector");
        Long robotId = createRobot(adminToken, inspectorId, "Forbidden Route Robot");
        Long routeId = createRoute(inspectorToken, robotId, "권한 테스트 경로");

        mockMvc.perform(post("/api/robot-routes")
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(createRouteRequest(robotId, "생성 불가 경로")))
                .andExpect(status().isForbidden());

        mockMvc.perform(put("/api/robot-routes/{routeId}", routeId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(createRouteRequest(robotId, "수정 불가 경로")))
                .andExpect(status().isForbidden());

        mockMvc.perform(delete("/api/robot-routes/{routeId}", routeId)
                        .header(HttpHeaders.AUTHORIZATION, bearer(viewerToken)))
                .andExpect(status().isForbidden());
    }

    private Long createRoute(String accessToken, Long robotId, String name) throws Exception {
        MvcResult result = mockMvc.perform(post("/api/robot-routes")
                        .header(HttpHeaders.AUTHORIZATION, bearer(accessToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(createRouteRequest(robotId, name)))
                .andExpect(status().isCreated())
                .andReturn();

        Number id = JsonPath.read(result.getResponse().getContentAsString(), "$.id");
        return id.longValue();
    }

    private String createRouteRequest(Long robotId, String name) {
        return """
                {
                  "robotId": %d,
                  "name": "%s",
                  "points": [
                    {
                      "pointOrder": 1,
                      "latitude": 37.5665,
                      "longitude": 126.978,
                      "pointType": "START"
                    },
                    {
                      "pointOrder": 2,
                      "latitude": 37.5651,
                      "longitude": 126.9792,
                      "pointType": "DESTINATION"
                    }
                  ]
                }
                """.formatted(robotId, name);
    }

    private Long createRobot(String accessToken, Long userId, String name) throws Exception {
        MvcResult result = mockMvc.perform(post("/api/robots")
                        .header(HttpHeaders.AUTHORIZATION, bearer(accessToken))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "userId": %d,
                                  "name": "%s",
                                  "serialNumber": "RB-%d"
                                }
                                """.formatted(userId, name, System.nanoTime())))
                .andExpect(status().isCreated())
                .andReturn();

        Number id = JsonPath.read(result.getResponse().getContentAsString(), "$.id");
        return id.longValue();
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
}
