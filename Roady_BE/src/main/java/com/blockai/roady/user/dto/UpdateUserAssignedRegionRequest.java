package com.blockai.roady.user.dto;

import jakarta.validation.constraints.Size;

public record UpdateUserAssignedRegionRequest(
        @Size(max = 10) String assignedRegionCode
) {
}
