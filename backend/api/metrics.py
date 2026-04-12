from prometheus_client import Counter, Histogram

# =============================================================================
# APPOINTMENT METRICS
# =============================================================================

# Track appointment lifecycle
appointments_created_total = Counter(
    "appointments_created_total",
    "Total number of appointments created",
    ["status", "speciality_id", "hospital_id"],
)

appointments_confirmed_total = Counter(
    "appointments_confirmed_total",
    "Total number of appointments confirmed",
    ["speciality_id", "hospital_id"],
)

appointments_cancelled_total = Counter(
    "appointments_cancelled_total",
    "Total number of appointments cancelled",
    ["cancellation_person", "speciality_id"],
)

appointments_completed_total = Counter(
    "appointments_completed_total",
    "Total number of appointments completed",
    ["speciality_id", "hospital_id"],
)

appointments_rescheduled_total = Counter(
    "appointments_rescheduled_total",
    "Total number of appointments rescheduled",
    ["speciality_id"],
)

# Track appointment duration in minutes
appointment_duration_minutes = Histogram(
    "appointment_duration_minutes",
    "Duration of appointments in minutes",
    ["speciality_name"],
    buckets=[30, 45, 60, 90, 120],
)

# Track appointment lead time (time between booking and appointment)
appointment_lead_time_hours = Histogram(
    "appointment_lead_time_hours",
    "Time between booking and appointment start in hours",
    ["status"],
    buckets=[1, 6, 12, 24, 48, 72, 168, 336, 720],  # 1hr to 30 days
)


# =============================================================================
# SLOTS METRICS
# =============================================================================
slots_generated_total = Counter(
    "slots_generated_total",
    "Total number of time slots generated",
    ["hospital_id", "status"],
)

# =============================================================================
# PROVIDER METRICS
# =============================================================================

# Provider performance
provider_appointments_total = Counter(
    "provider_appointments_total",
    "Total appointments per provider",
    ["provider_id", "speciality_name", "hospital_id"],
)


# =============================================================================
# PATIENT METRICS
# =============================================================================

# Patient activity
patients_registered_total = Counter(
    "patients_registered_total", "Total number of patient registrations", []
)


# =============================================================================
# HOSPITAL METRICS
# =============================================================================

hospital_appointments_total = Counter(
    "hospital_appointments_total",
    "Total appointments per hospital",
    ["hospital_id", "city", "state"],
)


# =============================================================================
# BUSINESS PERFORMANCE METRICS
# =============================================================================

revenue_generated = Counter(
    "revenue_generated_total",
    "Total revenue from appointments (sum of provider fees)",
    ["speciality_name", "hospital_id"],
)

cancellation_lead_time_hours = Histogram(
    "cancellation_lead_time_hours",
    "Time between booking and cancellation in hours",
    buckets=[1, 6, 12, 24, 48, 72, 168],
)


# =============================================================================
# HEALTHCARE-SPECIFIC ALERTS (for Prometheus AlertManager)
# =============================================================================


ALERTS = {
    "HighCancellationRate": {
        "expr": "rate(appointments_cancelled_total[1h]) / rate(appointments_created_total[1h]) > 0.2",
        "for": "15m",
        "severity": "warning",
        "description": "Cancellation rate >20% in the last hour",
    },
    "AppointmentBacklog": {
        "expr": "appointments_created_total - appointments_completed_total > 100",
        "for": "6h",
        "severity": "warning",
        "description": "More than 100 pending appointments",
    },
}
