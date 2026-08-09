package com.blockai.roady.damage.controller;

import com.blockai.roady.damage.domain.DamageFilterCriteria;
import com.blockai.roady.damage.dto.DamageDashboardSummaryResponse;
import com.blockai.roady.damage.service.DamageService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/dashboard/damages")
public class DamageDashboardController {

    private final DamageService damageService;

    public DamageDashboardController(DamageService damageService) {
        this.damageService = damageService;
    }

    @GetMapping("/summary")
    public DamageDashboardSummaryResponse getSummary(
            @RequestParam(value = "from", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime from,
            @RequestParam(value = "to", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime to,
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "robotId", required = false) Long robotId,
            @RequestParam(value = "assignedTo", required = false) Long assignedTo,
            @RequestParam(value = "regionCode", required = false) String regionCode
    ) {
        var criteria = new DamageFilterCriteria(from, to, status, robotId, assignedTo, regionCode);
        return DamageDashboardSummaryResponse.from(damageService.summarize(criteria));
    }
}
