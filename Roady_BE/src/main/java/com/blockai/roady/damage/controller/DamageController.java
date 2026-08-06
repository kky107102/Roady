package com.blockai.roady.damage.controller;

import com.blockai.roady.damage.domain.DamageImage;
import com.blockai.roady.damage.domain.DamageFilterCriteria;
import com.blockai.roady.damage.domain.DamageMapBounds;
import com.blockai.roady.damage.domain.DamageSearchCriteria;
import com.blockai.roady.damage.dto.CreateDamageRepairRequest;
import com.blockai.roady.damage.dto.CreateDamageAiAnalysisResponse;
import com.blockai.roady.damage.dto.DamageAiAnalysisResponse;
import com.blockai.roady.damage.dto.CompleteDamageRepairRequest;
import com.blockai.roady.damage.dto.DamageImageResponse;
import com.blockai.roady.damage.dto.DamageMapMarkerResponse;
import com.blockai.roady.damage.dto.DamageResponse;
import com.blockai.roady.damage.dto.DamageSearchResponse;
import com.blockai.roady.damage.dto.DamageSummaryResponse;
import com.blockai.roady.damage.dto.UpdateDamageReviewRequest;
import com.blockai.roady.damage.service.DamageAiAnalysisService;
import com.blockai.roady.damage.service.DamageService;
import com.blockai.roady.robot.service.RobotService;
import com.blockai.roady.security.AuthenticatedUser;
import jakarta.validation.Valid;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/damages")
public class DamageController {

    private final DamageService damageService;
    private final DamageAiAnalysisService aiAnalysisService;
    private final RobotService robotService;

    public DamageController(
            DamageService damageService,
            DamageAiAnalysisService aiAnalysisService,
            RobotService robotService
    ) {
        this.damageService = damageService;
        this.aiAnalysisService = aiAnalysisService;
        this.robotService = robotService;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseStatus(HttpStatus.CREATED)
    public DamageResponse createDamage(
            @AuthenticationPrincipal AuthenticatedUser user,
            @RequestParam(value = "robotId", required = false) Long robotId,
            @RequestParam(value = "assignedTo", required = false) Long assignedTo,
            @RequestParam(value = "description", required = false) String description,
            @RequestParam(value = "latitude", required = false) BigDecimal latitude,
            @RequestParam(value = "longitude", required = false) BigDecimal longitude,
            @RequestParam(value = "capturedAt", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime capturedAt,
            @RequestParam("images") List<MultipartFile> images
    ) {
        var damage = damageService.create(
                robotId,
                resolveReportedBy(user, robotId),
                assignedTo,
                description,
                latitude,
                longitude,
                capturedAt,
                images
        );
        aiAnalysisService.createAndEnqueue(damage.id());
        damage = damageService.getSummary(damage.id());
        var imageResponses = damageService.getImageMetadata(damage.id()).stream()
                .map(DamageImageResponse::from)
                .toList();
        return DamageResponse.from(damage, imageResponses);
    }

    private Long resolveReportedBy(AuthenticatedUser user, Long robotId) {
        if (user != null && user.id() != null) {
            return user.id();
        }
        if (robotId == null) {
            throw new IllegalArgumentException("robotId is required for unauthenticated robot damage uploads.");
        }
        return robotService.get(robotId).getUserId();
    }

    @GetMapping
    public DamageSearchResponse getDamages(
            @RequestParam(value = "from", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime from,
            @RequestParam(value = "to", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime to,
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "robotId", required = false) Long robotId,
            @RequestParam(value = "assignedTo", required = false) Long assignedTo,
            @RequestParam(value = "regionCode", required = false) String regionCode,
            @RequestParam(value = "keyword", required = false) String keyword,
            @RequestParam(value = "page", defaultValue = "0") int page,
            @RequestParam(value = "size", defaultValue = "20") int size
    ) {
        var criteria = new DamageSearchCriteria(
                from,
                to,
                status,
                robotId,
                assignedTo,
                regionCode,
                keyword,
                page,
                size
        );
        return DamageSearchResponse.from(damageService.search(criteria));
    }

    @GetMapping("/map-markers")
    public List<DamageMapMarkerResponse> getMapMarkers(
            @RequestParam(value = "from", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime from,
            @RequestParam(value = "to", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime to,
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "robotId", required = false) Long robotId,
            @RequestParam(value = "assignedTo", required = false) Long assignedTo,
            @RequestParam(value = "regionCode", required = false) String regionCode,
            @RequestParam("south") BigDecimal south,
            @RequestParam("north") BigDecimal north,
            @RequestParam("west") BigDecimal west,
            @RequestParam("east") BigDecimal east
    ) {
        var criteria = new DamageFilterCriteria(from, to, status, robotId, assignedTo, regionCode);
        var bounds = new DamageMapBounds(south, north, west, east);
        return damageService.findMapMarkers(criteria, bounds).stream()
                .map(DamageMapMarkerResponse::from)
                .toList();
    }

    @GetMapping("/{damageId}")
    public DamageResponse getDamage(@PathVariable Long damageId) {
        var damage = damageService.getSummary(damageId);
        var imageResponses = damageService.getImageMetadata(damageId).stream()
                .map(DamageImageResponse::from)
                .toList();
        return DamageResponse.from(damage, imageResponses);
    }

    @PatchMapping("/{damageId}/review")
    public DamageSummaryResponse updateDamageReview(
            @PathVariable Long damageId,
            @RequestBody UpdateDamageReviewRequest request
    ) {
        return DamageSummaryResponse.from(damageService.updateReview(
                damageId,
                request.status(),
                request.processingPriority(),
                request.reviewDamageType(),
                request.reviewNote()
        ));
    }

    @PostMapping("/{damageId}/repair-request")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public DamageSummaryResponse createDamageRepairRequest(
            @AuthenticationPrincipal AuthenticatedUser user,
            @PathVariable Long damageId,
            @Valid @RequestBody CreateDamageRepairRequest request
    ) {
        return DamageSummaryResponse.from(damageService.requestRepair(
                damageId,
                user.id(),
                request.processingPriority(),
                request.reviewDamageType(),
                request.repairerId(),
                request.note()
        ));
    }

    @PatchMapping("/{damageId}/repair-request")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public DamageSummaryResponse updateDamageRepairRequest(
            @AuthenticationPrincipal AuthenticatedUser user,
            @PathVariable Long damageId,
            @Valid @RequestBody CreateDamageRepairRequest request
    ) {
        return DamageSummaryResponse.from(damageService.updateRepairRequest(
                damageId,
                user.id(),
                request.processingPriority(),
                request.reviewDamageType(),
                request.repairerId(),
                request.note()
        ));
    }

    @PatchMapping("/{damageId}/repair-complete")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public DamageSummaryResponse completeDamageRepair(
            @AuthenticationPrincipal AuthenticatedUser user,
            @PathVariable Long damageId,
            @Valid @RequestBody CompleteDamageRepairRequest request
    ) {
        return DamageSummaryResponse.from(damageService.completeRepair(
                damageId,
                user.id(),
                request.completedAt(),
                request.note()
        ));
    }

    @PatchMapping("/{damageId}/repair-cancel")
    @PreAuthorize("hasAnyRole('ADMIN', 'INSPECTOR')")
    public DamageSummaryResponse cancelDamageRepair(
            @AuthenticationPrincipal AuthenticatedUser user,
            @PathVariable Long damageId,
            @Valid @RequestBody CreateDamageRepairRequest request
    ) {
        return DamageSummaryResponse.from(damageService.cancelRepair(
                damageId,
                user.id(),
                request.note()
        ));
    }

    @PostMapping("/{damageId}/analysis-jobs")
    @ResponseStatus(HttpStatus.ACCEPTED)
    public CreateDamageAiAnalysisResponse createDamageAnalysisJob(@PathVariable Long damageId) {
        var analysisResult = aiAnalysisService.createAndEnqueue(damageId);
        return new CreateDamageAiAnalysisResponse(DamageAiAnalysisResponse.from(analysisResult));
    }

    @GetMapping("/{damageId}/analysis-jobs")
    public List<DamageAiAnalysisResponse> getDamageAnalysisJobs(@PathVariable Long damageId) {
        return aiAnalysisService.getAnalysisResultsByDamageId(damageId).stream()
                .map(DamageAiAnalysisResponse::from)
                .toList();
    }

    @GetMapping("/{damageId}/images/{imageId}/content")
    public ResponseEntity<byte[]> getDamageImage(
            @PathVariable Long damageId,
            @PathVariable Long imageId
    ) {
        DamageImage image = damageService.getImage(damageId, imageId);

        ContentDisposition disposition = ContentDisposition.inline()
                .filename(image.getOriginalFilename(), StandardCharsets.UTF_8)
                .build();

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(image.getContentType()))
                .contentLength(image.getSizeBytes())
                .header(HttpHeaders.CONTENT_DISPOSITION, disposition.toString())
                .body(image.getData());
    }
}
