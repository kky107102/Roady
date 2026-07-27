package com.blockai.roady.damage.controller;

import com.blockai.roady.damage.dto.DamageAiAnalysisResponse;
import com.blockai.roady.damage.service.DamageAiAnalysisService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/damage-ai-analysis-results")
public class DamageAiAnalysisController {

    private final DamageAiAnalysisService aiAnalysisService;

    public DamageAiAnalysisController(DamageAiAnalysisService aiAnalysisService) {
        this.aiAnalysisService = aiAnalysisService;
    }

    @GetMapping("/{analysisResultId}")
    public DamageAiAnalysisResponse getDamageAiAnalysisResult(@PathVariable Long analysisResultId) {
        return DamageAiAnalysisResponse.from(aiAnalysisService.getAnalysisResult(analysisResultId));
    }
}
