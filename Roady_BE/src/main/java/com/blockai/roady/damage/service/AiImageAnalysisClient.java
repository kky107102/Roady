package com.blockai.roady.damage.service;

import com.blockai.roady.damage.config.AiImageAnalysisProperties;
import com.blockai.roady.damage.domain.DamageImage;
import com.blockai.roady.damage.domain.DamageSummary;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClient;

import java.nio.charset.StandardCharsets;
import java.util.List;

@Component
public class AiImageAnalysisClient {

    private final RestClient restClient;
    private final AiImageAnalysisProperties properties;

    public AiImageAnalysisClient(RestClient aiImageAnalysisRestClient, AiImageAnalysisProperties properties) {
        this.restClient = aiImageAnalysisRestClient;
        this.properties = properties;
    }

    public String analyze(DamageSummary damage, List<DamageImage> images) {
        if (!StringUtils.hasText(properties.getEndpointUrl())) {
            throw new IllegalStateException("AI image analysis endpoint URL is not configured.");
        }

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("damageId", damage.id().toString());
        body.add("latitude", valueOrEmpty(damage.latitude()));
        body.add("longitude", valueOrEmpty(damage.longitude()));
        body.add("capturedAt", valueOrEmpty(damage.capturedAt()));

        for (DamageImage image : images) {
            body.add("images", new NamedByteArrayResource(image.getData(), image.getOriginalFilename()));
        }

        byte[] responseBody = restClient.post()
                .uri(properties.getEndpointUrl())
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(body)
                .retrieve()
                .body(byte[].class);

        return responseBody == null ? null : new String(responseBody, StandardCharsets.UTF_8);
    }

    private String valueOrEmpty(Object value) {
        return value == null ? "" : value.toString();
    }

    private static class NamedByteArrayResource extends ByteArrayResource {

        private final String filename;

        private NamedByteArrayResource(byte[] byteArray, String filename) {
            super(byteArray);
            this.filename = filename;
        }

        @Override
        public String getFilename() {
            return filename;
        }
    }
}
