"""
Learning Content Manager — AJAX views.

Provides full CRUD for:
  - EAPart   (Module)
  - EADomain (Domain)
  - EATopic  (Topic) incl. E-Book & Video content
"""

import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction

from ea_exam.models import EAPart, EADomain, EATopic


# ─── Permission helper ────────────────────────────────────────────────────────

def _require_staff(request):
    """Return HttpResponseForbidden if user is not staff/superuser, else None."""
    if not (request.user.is_active and (request.user.is_staff or request.user.is_superuser)):
        return HttpResponseForbidden("Staff access required.")
    return None


# ─── Main page ────────────────────────────────────────────────────────────────

@login_required
def learning_manager(request):
    """Render the unified Learning Content Manager page."""
    denied = _require_staff(request)
    if denied:
        return denied

    modules = (
        EAPart.objects
        .prefetch_related("domains__topics")
        .order_by("number")
    )
    return render(request, "setting/learning_manager.html", {
        "title": "Learning Content Manager",
        "modules": modules,
    })


# ─── Module (EAPart) CRUD ─────────────────────────────────────────────────────

@login_required
@require_POST
def module_add(request):
    """Create a new EAPart (Module). Returns updated module row HTML + new module id."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    name        = request.POST.get("name", "").strip()
    number      = request.POST.get("number", "").strip()
    description = request.POST.get("description", "").strip()
    is_active   = request.POST.get("is_active") == "true"

    if not name or not number:
        return JsonResponse({"error": "Name and number are required."}, status=400)

    if not number.isdigit():
        return JsonResponse({"error": "Number must be a positive integer."}, status=400)

    if EAPart.objects.filter(number=int(number)).exists():
        return JsonResponse({"error": f"Module number {number} already exists."}, status=400)

    module = EAPart.objects.create(
        name=name,
        number=int(number),
        description=description,
        is_active=is_active,
    )
    html = render(request, "setting/partials/module_row.html", {"module": module}).content.decode()
    return JsonResponse({"ok": True, "id": module.pk, "html": html})


@login_required
@require_POST
def module_save(request, pk):
    """Rename / toggle active on an EAPart."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    module = get_object_or_404(EAPart, pk=pk)

    name        = request.POST.get("name", "").strip()
    description = request.POST.get("description", module.description).strip()
    is_active   = request.POST.get("is_active")
    number      = request.POST.get("number", "").strip()

    if name:
        module.name = name
    if number and number.isdigit():
        new_num = int(number)
        if new_num != module.number and EAPart.objects.filter(number=new_num).exists():
            return JsonResponse({"error": f"Module number {new_num} already exists."}, status=400)
        module.number = new_num
    module.description = description
    if is_active is not None:
        module.is_active = (is_active == "true")
    module.save()

    html = render(request, "setting/partials/module_row.html", {"module": module}).content.decode()
    return JsonResponse({"ok": True, "name": module.name, "is_active": module.is_active, "html": html})


@login_required
@require_POST
def module_delete(request, pk):
    """Delete an EAPart and cascade-delete all domains/topics inside it."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    module = get_object_or_404(EAPart, pk=pk)
    module.delete()
    return JsonResponse({"ok": True})


# ─── Domain (EADomain) CRUD ───────────────────────────────────────────────────

@login_required
@require_POST
def domain_add(request):
    """Create a new EADomain under a given EAPart."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    module_id = request.POST.get("module_id", "").strip()
    name      = request.POST.get("name", "").strip()
    order     = request.POST.get("order", "0").strip()

    if not module_id or not name:
        return JsonResponse({"error": "module_id and name are required."}, status=400)

    module = get_object_or_404(EAPart, pk=module_id)
    domain = EADomain.objects.create(
        part=module,
        name=name,
        order=int(order) if order.isdigit() else 0,
    )
    html = render(request, "setting/partials/domain_row.html", {"domain": domain}).content.decode()
    return JsonResponse({"ok": True, "id": domain.pk, "html": html})


@login_required
@require_POST
def domain_save(request, pk):
    """Rename or reorder an EADomain."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    domain = get_object_or_404(EADomain, pk=pk)

    name  = request.POST.get("name", "").strip()
    order = request.POST.get("order", "").strip()

    if name:
        domain.name = name
    if order.isdigit():
        domain.order = int(order)
    domain.save()

    html = render(request, "setting/partials/domain_row.html", {"domain": domain}).content.decode()
    return JsonResponse({"ok": True, "name": domain.name, "html": html})


@login_required
@require_POST
def domain_delete(request, pk):
    """Delete an EADomain and cascade-delete all topics inside it."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    domain = get_object_or_404(EADomain, pk=pk)
    domain.delete()
    return JsonResponse({"ok": True})


# ─── Topic (EATopic) CRUD ─────────────────────────────────────────────────────

@login_required
@require_GET
def topic_editor(request, pk):
    """Return the topic editor partial for the right panel (AJAX GET)."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    topic = get_object_or_404(
        EATopic.objects.select_related("domain__part"), pk=pk
    )
    domains = EADomain.objects.select_related("part").order_by("part__number", "order")
    html = render(request, "setting/partials/topic_editor.html", {
        "topic": topic,
        "domains": domains,
        "is_new": False,
    }).content.decode()
    return JsonResponse({"ok": True, "html": html})


@login_required
@require_GET
def topic_editor_new(request):
    """Return a blank topic editor form for a given domain (AJAX GET)."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    domain_id = request.GET.get("domain")
    domain = get_object_or_404(EADomain, pk=domain_id) if domain_id else None
    domains = EADomain.objects.select_related("part").order_by("part__number", "order")
    html = render(request, "setting/partials/topic_editor.html", {
        "topic": None,
        "selected_domain": domain,
        "domains": domains,
        "is_new": True,
    }).content.decode()
    return JsonResponse({"ok": True, "html": html})


@login_required
@require_POST
def topic_save(request, pk):
    """Save an existing EATopic (name, order, ebook, video)."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    topic = get_object_or_404(EATopic, pk=pk)

    name                = request.POST.get("name", "").strip()
    order               = request.POST.get("order", "").strip()
    domain_id           = request.POST.get("domain_id", "").strip()
    supabase_pdf_path   = request.POST.get("supabase_pdf_path", "").strip()
    video_external_url  = request.POST.get("video_external_url", "").strip()

    if not name:
        return JsonResponse({"error": "Topic name is required."}, status=400)

    topic.name = name
    if order.isdigit():
        topic.order = int(order)
    if domain_id:
        topic.domain = get_object_or_404(EADomain, pk=domain_id)
    topic.supabase_pdf_path  = supabase_pdf_path
    topic.video_external_url = video_external_url

    # Handle file uploads
    if "pdf_file" in request.FILES:
        topic.pdf_file = request.FILES["pdf_file"]
    elif request.POST.get("clear_pdf") == "true":
        topic.pdf_file = None

    if "video_file" in request.FILES:
        topic.video_file = request.FILES["video_file"]
    elif request.POST.get("clear_video") == "true":
        topic.video_file = None

    topic.save()

    # Re-render topic row for tree update
    row_html = render(request, "setting/partials/topic_row.html", {"topic": topic}).content.decode()
    return JsonResponse({
        "ok": True,
        "id": topic.pk,
        "name": topic.name,
        "has_ebook": bool(topic.pdf_file or topic.supabase_pdf_path),
        "has_video": bool(topic.video_file or topic.video_external_url),
        "row_html": row_html,
    })


@login_required
@require_POST
def topic_create(request):
    """Create a new EATopic under a given domain."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    name                = request.POST.get("name", "").strip()
    domain_id           = request.POST.get("domain_id", "").strip()
    order               = request.POST.get("order", "0").strip()
    supabase_pdf_path   = request.POST.get("supabase_pdf_path", "").strip()
    video_external_url  = request.POST.get("video_external_url", "").strip()

    if not name or not domain_id:
        return JsonResponse({"error": "Name and domain are required."}, status=400)

    domain = get_object_or_404(EADomain, pk=domain_id)

    topic = EATopic(
        name=name,
        domain=domain,
        order=int(order) if order.isdigit() else 0,
        supabase_pdf_path=supabase_pdf_path,
        video_external_url=video_external_url,
    )
    if "pdf_file" in request.FILES:
        topic.pdf_file = request.FILES["pdf_file"]
    if "video_file" in request.FILES:
        topic.video_file = request.FILES["video_file"]
    topic.save()

    row_html = render(request, "setting/partials/topic_row.html", {"topic": topic}).content.decode()
    return JsonResponse({
        "ok": True,
        "id": topic.pk,
        "domain_id": domain.pk,
        "name": topic.name,
        "has_ebook": bool(topic.pdf_file or topic.supabase_pdf_path),
        "has_video": bool(topic.video_file or topic.video_external_url),
        "row_html": row_html,
    })


@login_required
@require_POST
def topic_delete(request, pk):
    """Delete an EATopic."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    topic = get_object_or_404(EATopic, pk=pk)
    domain_id = topic.domain_id
    topic.delete()
    return JsonResponse({"ok": True, "domain_id": domain_id})
