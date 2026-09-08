from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import EAPart, EAQuestion
from core.models import BlogArticle
from .programmatic_data import get_programmatic_page, get_all_programmatic_urls

def about_view(request):
    """Public About page — RISE360 Institute story, founder, and collaboration."""
    highlights = [
        ("infinity",      "#ecfdf5", "#10b981", "500+ Free MCQs",          "Practice without paying. Our free MCQ bank covers all 3 EA exam parts with full explanations."),
        ("flask",         "#eff6ff", "#3b82f6", "Prometric Simulations",    "Timed, full-length exam simulations that mirror the real IRS testing experience."),
        ("chart-line",    "#fefce8", "#ca8a04", "Live Progress Analytics",  "Domain-level accuracy tracking, readiness scores, and study streaks — all updated in real time."),
        ("book-open",     "#fdf4ff", "#9333ea", "Tom Norton Study Material","Official lectures and books by Tom Norton CPA, EA — integrated directly into the LMS."),
    ]
    return render(request, "public_pages/about.html", {
        "title": "About RISE360 Institute — EA Exam Prep by Hiren Soni CA & Tom Norton CPA, EA",
        "highlights": highlights,
    })



def public_home_view(request):
    """Public landing page at the root domain for SEO."""
    recent_blogs = []
    try:
        recent_blogs = list(BlogArticle.objects.filter(is_published=True)[:3])
    except Exception:
        pass
    return render(request, "public_pages/home.html", {
        "title": "RISE360 Institute — Next-Generation Learning Management Platform",
        "recent_blogs": recent_blogs,
    })

def free_practice_test_view(request):
    """Free EA Exam Practice Questions — All 3 Parts"""
    parts = []
    questions_by_part = {}
    try:
        parts = EAPart.objects.all().order_by("number")
        for part in parts:
            questions = EAQuestion.objects.filter(part=part, status="active")[:10]
            questions_by_part[part] = questions
    except Exception:
        pass
    return render(request, "public_pages/free_practice_test.html", {
        "title": "Free EA Exam Practice Questions — All 3 Parts",
        "questions_by_part": questions_by_part,
    })

def public_part_view(request, part_number):
    """Public SEO page for each EA Part."""
    part = get_object_or_404(EAPart, number=part_number)
    titles = {
        1: "EA Exam Part 1: Individual Taxation — Study Guide + Free MCQs",
        2: "EA Exam Part 2: Business Taxation — Practice Questions",
        3: "EA Exam Part 3: Representation — Free Quiz"
    }
    part_links = [
        (1, "Individual Taxation"),
        (2, "Business Taxation"),
        (3, "Representation"),
    ]
    return render(request, "public_pages/part_detail.html", {
        "title": titles.get(part.number, f"EA Exam Part {part.number} Prep"),
        "part": part,
        "part_links": part_links,
    })

def sitemap_view(request):
    """Dynamic XML sitemap for Google Search Console."""
    from django.http import HttpResponse
    from django.utils.timezone import now
    parts = EAPart.objects.all()
    blogs = BlogArticle.objects.filter(is_published=True)
    base = "https://www.rise360institute.com"
    today = now().strftime("%Y-%m-%d")

    urls = [
        f"{base}/",
        f"{base}/en/ea/",
        f"{base}/en/ea/free-practice-test/",
        f"{base}/en/ea/blog/",
        f"{base}/en/ea/about/",
    ]
    for p in parts:
        urls.append(f"{base}/en/ea/part/{p.number}/")
    for b in blogs:
        urls.append(f"{base}/en/ea/blog/{b.slug}/")
    for cat, slug in get_all_programmatic_urls():
        urls.append(f"{base}/en/ea/{cat}/{slug}/")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n"
    xml += '</urlset>'

    return HttpResponse(xml, content_type="application/xml")

def blog_list_view(request):
    """Public SEO blog index page."""
    articles = BlogArticle.objects.filter(is_published=True)
    return render(request, "public_pages/blog_list.html", {
        "title": "EA Exam Prep Blog | RISE360 Institute",
        "articles": articles,
    })

def blog_detail_view(request, slug):
    """Public SEO blog detail page."""
    article = get_object_or_404(BlogArticle, slug=slug, is_published=True)
    return render(request, "public_pages/blog_detail.html", {
        "title": f"{article.title} | RISE360 Institute",
        "article": article,
    })



def programmatic_seo_view(request, slug, category):
    """Dynamically serves programmatic tax guides, forms, glossary and state pages."""
    data = get_programmatic_page(category, slug)
    if not data:
        raise Http404("Tax topic not found")
    
    return render(request, "public_pages/programmatic_detail.html", {
        "data": data,
        "category": category,
        "slug": slug
    })
