from django.http import JsonResponse


def health_check(request):
    """Trivial liveness endpoint used by Docker/deploy health checks and CI."""
    return JsonResponse({"status": "ok"})
