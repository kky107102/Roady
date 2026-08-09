package com.blockai.roady.damage.service;

import com.blockai.roady.damage.config.AiImageAnalysisProperties;
import com.blockai.roady.damage.domain.DamageImage;
import com.blockai.roady.damage.domain.DamageSummary;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class AiImageAnalysisClientTest {

    @Test
    void analyzeDecodesJsonResponseAsUtf8WhenCharsetIsMissing() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        AiImageAnalysisProperties properties = new AiImageAnalysisProperties();
        properties.setEndpointUrl("http://ai:8000/analyze");
        AiImageAnalysisClient client = new AiImageAnalysisClient(builder.build(), properties);
        String rawResult = "{\"estimated_severity_label\":\"정상 추정\"}";

        server.expect(requestTo("http://ai:8000/analyze"))
                .andRespond(withSuccess(
                        rawResult.getBytes(StandardCharsets.UTF_8),
                        MediaType.APPLICATION_JSON
                ));

        String result = client.analyze(summary(1L), List.of(image(1L, 1L)));

        assertThat(result).isEqualTo(rawResult);
        server.verify();
    }

    private DamageSummary summary(Long damageId) {
        LocalDateTime now = LocalDateTime.of(2026, 8, 7, 15, 0);
        return new DamageSummary(
                damageId,
                null,
                2L,
                null,
                "AI v2 integration test",
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                now,
                "COLLECTED",
                null,
                null,
                null,
                1L,
                now,
                now
        );
    }

    private DamageImage image(Long imageId, Long damageId) {
        LocalDateTime now = LocalDateTime.of(2026, 8, 7, 15, 0);
        return new DamageImage(
                imageId,
                damageId,
                1,
                "damage.png",
                "image/png",
                3L,
                new byte[]{1, 2, 3},
                now
        );
    }
}
