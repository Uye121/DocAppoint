from django.core.management import call_command
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from api.utils.env import env


@csrf_exempt
@require_http_methods(["POST"])
@never_cache
def trigger_slot_management(request):
    """
    Endpoint to trigger slot cleanup and generation.
    Designed to be called by cron-job.org.
    """
    auth_header = request.headers.get("Authorization", "")
    expected_token = env.str("CRON_SECRET_TOKEN", "")

    if not expected_token or auth_header != f"Bearer {expected_token}":
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        call_command("handle_slots", purge=True, generate=True)

        return JsonResponse(
            {"status": "success", "message": "Slots purged and generated successfully"}
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
