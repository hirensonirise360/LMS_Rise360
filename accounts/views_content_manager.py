"""
Learning Content Manager — AJAX views.

Provides full CRUD for:
  - EAPart   (Module)
  - EADomain (Domain)
  - EATopic  (Topic) incl. E-Book & Video content
"""

import json
import re
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction

from ea_exam.models import EAPart, EADomain, EATopic, EATopicEbookFile


# ─── Permission helper ────────────────────────────────────────────────────────

def _require_staff(request):
    """Return HttpResponseForbidden / JsonResponse if user is not authorized, else None."""
    is_authorized = request.user.is_active and (
        request.user.is_staff 
        or request.user.is_superuser 
        or getattr(request.user, 'is_lecturer', False)
        or getattr(request.user, 'is_dep_head', False)
    )
    if not is_authorized:
        if (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or request.content_type == "application/json"
            or request.method == "POST"
        ):
            return JsonResponse({"ok": False, "error": "Access Denied: Staff or Administrator permissions required."}, status=403)
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
        .prefetch_related(
            "domains__topics__ebook_files",
            "domains__topics__resources",
        )
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
def module_reorder(request):
    """Reorder EAPart (modules) from a list of module IDs."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
        order_ids = data.get("order")
    except Exception:
        order_ids = None

    if not order_ids:
        order_ids = request.POST.getlist("order[]") or request.POST.getlist("order")

    if not order_ids:
        return JsonResponse({"error": "No order data provided."}, status=400)

    try:
        with transaction.atomic():
            modules = list(EAPart.objects.filter(pk__in=order_ids))
            id_map = {str(m.pk): m for m in modules}

            # Step 1: Temporarily shift numbers to high values to prevent unique constraint collision
            for i, module_id in enumerate(order_ids):
                m_id = str(module_id)
                if m_id in id_map:
                    id_map[m_id].number = 10000 + i + 1
                    id_map[m_id].save(update_fields=["number"])

            # Step 2: Assign new sequential numbers
            for idx, module_id in enumerate(order_ids, start=1):
                m_id = str(module_id)
                if m_id in id_map:
                    id_map[m_id].number = idx
                    id_map[m_id].save(update_fields=["number"])

        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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


from django.db.models import Max


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
    order     = request.POST.get("order", "").strip()

    if not module_id or not name:
        return JsonResponse({"error": "module_id and name are required."}, status=400)

    module = get_object_or_404(EAPart, pk=module_id)

    if order.isdigit():
        order_val = int(order)
    else:
        max_order = EADomain.objects.filter(part=module).aggregate(m=Max("order"))["m"] or 0
        order_val = max_order + 1

    domain = EADomain.objects.create(
        part=module,
        name=name,
        order=order_val,
    )
    html = render(request, "setting/partials/domain_row.html", {"domain": domain}).content.decode()
    return JsonResponse({
        "ok": True,
        "id": domain.pk,
        "name": domain.name,
        "module_id": module.pk,
        "module_name": module.name,
        "domain_count": module.domains.count(),
        "html": html,
    })


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
def domain_reorder(request):
    """Reorder EADomain (domains) within or across modules."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
        order_ids = data.get("order")
        module_id = data.get("module_id")
    except Exception:
        order_ids = None
        module_id = None

    if not order_ids:
        order_ids = request.POST.getlist("order[]") or request.POST.getlist("order")
        module_id = request.POST.get("module_id")

    if not order_ids:
        return JsonResponse({"error": "No order data provided."}, status=400)

    try:
        with transaction.atomic():
            domains = list(EADomain.objects.filter(pk__in=order_ids))
            id_map = {str(d.pk): d for d in domains}
            
            for idx, domain_id in enumerate(order_ids, start=1):
                d_id = str(domain_id)
                if d_id in id_map:
                    dom = id_map[d_id]
                    dom.order = idx
                    if module_id:
                        dom.part_id = int(module_id)
                    dom.save(update_fields=["order", "part"] if module_id else ["order"])

        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_POST
def domain_delete(request, pk):
    """Delete an EADomain and cascade-delete all topics inside it."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    domain = get_object_or_404(EADomain, pk=pk)
    module_id = domain.part_id
    domain.delete()
    domain_count = EADomain.objects.filter(part_id=module_id).count()
    return JsonResponse({"ok": True, "module_id": module_id, "domain_count": domain_count})


# ─── Topic (EATopic) CRUD ─────────────────────────────────────────────────────

@login_required
@require_GET
def topic_editor(request, pk):
    """Return the topic editor partial for the right panel (AJAX GET)."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    topic = get_object_or_404(
        EATopic.objects.select_related("domain__part").prefetch_related("ebook_files", "resources"), pk=pk
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
    next_order = 1
    if domain:
        next_order = (domain.topics.aggregate(m=Max("order"))["m"] or 0) + 1
    html = render(request, "setting/partials/topic_editor.html", {
        "topic": None,
        "next_order": next_order,
        "selected_domain": domain,
        "domains": domains,
        "is_new": True,
    }).content.decode()
    return JsonResponse({"ok": True, "html": html})


@login_required
@require_POST
def topic_save(request, pk):
    """Save an existing EATopic (name, order, ebook, video, question_file)."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    topic = get_object_or_404(EATopic, pk=pk)

    name                    = request.POST.get("name", "").strip()
    order                   = request.POST.get("order", "").strip()
    domain_id               = request.POST.get("domain_id", "").strip()
    supabase_pdf_path       = request.POST.get("supabase_pdf_path", "").strip()
    supabase_question_path  = request.POST.get("supabase_question_path", "").strip()
    video_external_url      = request.POST.get("video_external_url", "").strip()

    if video_external_url:
        iframe_match = re.search(r'src=["\']([^"\']+)["\']', video_external_url)
        if iframe_match:
            video_external_url = iframe_match.group(1).strip()

    if not name:
        return JsonResponse({"error": "Topic name is required."}, status=400)

    topic.name = name
    if order.isdigit():
        topic.order = int(order)
    if domain_id:
        topic.domain = get_object_or_404(EADomain, pk=domain_id)
    topic.supabase_pdf_path      = supabase_pdf_path
    topic.supabase_question_path = supabase_question_path
    topic.video_external_url     = video_external_url

    # Handle multiple / single E-Book file uploads
    uploaded_pdf_files = request.FILES.getlist("pdf_files") or request.FILES.getlist("pdf_file")
    for f in uploaded_pdf_files:
        if not EATopicEbookFile.objects.filter(topic=topic, title=f.name).exists():
            try:
                EATopicEbookFile.objects.create(topic=topic, pdf_file=f, title=f.name)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error uploading material '{f.name}': {e}")
                return JsonResponse({"ok": False, "error": f"Failed to upload '{f.name}': {e}"}, status=500)

    # Handle deleted ebook file IDs
    delete_ebook_ids = request.POST.getlist("delete_ebook_ids")
    if delete_ebook_ids:
        EATopicEbookFile.objects.filter(topic=topic, pk__in=delete_ebook_ids).delete()

    if request.POST.get("clear_pdf") == "true":
        topic.pdf_file = None
        topic.supabase_pdf_path = ""
        topic.ebook_files.all().delete()

    try:
        if "video_file" in request.FILES:
            topic.video_file = request.FILES["video_file"]
        elif request.POST.get("clear_video") == "true":
            topic.video_file = None

        if "question_file" in request.FILES:
            topic.question_file = request.FILES["question_file"]
        elif request.POST.get("clear_question_file") == "true":
            topic.question_file = None

        topic.save()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error saving topic files: {e}")
        return JsonResponse({"ok": False, "error": f"Storage error: {e}"}, status=500)

    # Re-render topic row for tree update
    row_html = render(request, "setting/partials/topic_row.html", {"topic": topic}).content.decode()
    return JsonResponse({
        "ok": True,
        "id": topic.pk,
        "name": topic.name,
        "has_ebook": topic.has_ebook if hasattr(topic, 'has_ebook') else bool(topic.pdf_file or topic.supabase_pdf_path or topic.ebook_files.exists()),
        "ebook_count": topic.ebook_count,
        "has_video": bool(topic.video_file or topic.video_external_url),
        "has_question_file": bool(topic.question_file or topic.supabase_question_path),
        "row_html": row_html,
    })


@login_required
@require_POST
def topic_ebook_delete(request, file_id):
    """Delete an individual E-Book file from a topic."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    ebook_file = get_object_or_404(EATopicEbookFile, pk=file_id)
    topic_id = ebook_file.topic_id
    ebook_file.delete()
    return JsonResponse({"ok": True, "topic_id": topic_id})


@login_required
@require_POST
def topic_create(request):
    """Create a new EATopic under a given domain."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    name                    = request.POST.get("name", "").strip()
    domain_id               = request.POST.get("domain_id", "").strip()
    order                   = request.POST.get("order", "0").strip()
    supabase_pdf_path       = request.POST.get("supabase_pdf_path", "").strip()
    supabase_question_path  = request.POST.get("supabase_question_path", "").strip()
    video_external_url      = request.POST.get("video_external_url", "").strip()

    if video_external_url:
        iframe_match = re.search(r'src=["\']([^"\']+)["\']', video_external_url)
        if iframe_match:
            video_external_url = iframe_match.group(1).strip()

    if not name or not domain_id:
        return JsonResponse({"error": "Name and domain are required."}, status=400)

    domain = get_object_or_404(EADomain, pk=domain_id)

    topic = EATopic(
        name=name,
        domain=domain,
        order=int(order) if order.isdigit() else 0,
        supabase_pdf_path=supabase_pdf_path,
        supabase_question_path=supabase_question_path,
        video_external_url=video_external_url,
    )
    if "pdf_file" in request.FILES:
        topic.pdf_file = request.FILES["pdf_file"]
    if "video_file" in request.FILES:
        topic.video_file = request.FILES["video_file"]
    if "question_file" in request.FILES:
        topic.question_file = request.FILES["question_file"]
    topic.save()

    uploaded_pdf_files = request.FILES.getlist("pdf_files")
    for f in uploaded_pdf_files:
        if not EATopicEbookFile.objects.filter(topic=topic, title=f.name).exists():
            EATopicEbookFile.objects.create(topic=topic, pdf_file=f, title=f.name)

    row_html = render(request, "setting/partials/topic_row.html", {"topic": topic}).content.decode()
    return JsonResponse({
        "ok": True,
        "id": topic.pk,
        "domain_id": domain.pk,
        "name": topic.name,
        "has_ebook": topic.has_ebook if hasattr(topic, 'has_ebook') else bool(topic.pdf_file or topic.supabase_pdf_path or topic.ebook_files.exists()),
        "ebook_count": topic.ebook_count,
        "has_video": bool(topic.video_file or topic.video_external_url),
        "has_question_file": bool(topic.question_file or topic.supabase_question_path),
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


@login_required
@require_POST
def topic_reorder(request):
    """Reorder EATopic (topics) within or across domains."""
    denied = _require_staff(request)
    if denied:
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
        order_ids = data.get("order")
        domain_id = data.get("domain_id")
    except Exception:
        order_ids = None
        domain_id = None

    if not order_ids:
        order_ids = request.POST.getlist("order[]") or request.POST.getlist("order")
        domain_id = request.POST.get("domain_id")

    if not order_ids:
        return JsonResponse({"error": "No order data provided."}, status=400)

    try:
        with transaction.atomic():
            topics = list(EATopic.objects.filter(pk__in=order_ids))
            id_map = {str(t.pk): t for t in topics}

            for idx, topic_id in enumerate(order_ids, start=1):
                t_id = str(topic_id)
                if t_id in id_map:
                    top = id_map[t_id]
                    top.order = idx
                    if domain_id:
                        top.domain_id = int(domain_id)
                    top.save(update_fields=["order", "domain"] if domain_id else ["order"])

        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

