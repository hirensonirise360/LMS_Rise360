from django.http import JsonResponse
from django.shortcuts import render


def _is_json_request(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return True
    accepted = request.headers.get("accept", "")
    return "application/json" in accepted


def bad_request(request, exception):
    if _is_json_request(request):
        return JsonResponse({"success": False, "error": "Bad request."}, status=400)
    return render(request, "400.html", status=400)


def permission_denied(request, exception):
    if _is_json_request(request):
        return JsonResponse({"success": False, "error": "Permission denied."}, status=403)
    return render(request, "403.html", status=403)


def page_not_found(request, exception):
    if _is_json_request(request):
        return JsonResponse({"success": False, "error": "Not found."}, status=404)
    return render(request, "404.html", status=404)


def server_error(request):
    if _is_json_request(request):
        return JsonResponse({"success": False, "error": "Server error."}, status=500)
    return render(request, "500.html", status=500)
