from django.urls import path
from . import views
from . import public_views

urlpatterns = [
    # Public SEO Pages
    path("", public_views.public_home_view, name="ea_public_home"),
    path("free-practice-test/", public_views.free_practice_test_view, name="free_practice_test"),
    path("part/<int:part_number>/", public_views.public_part_view, name="part_detail"),
    path("blog/", public_views.blog_list_view, name="blog_list"),
    path("blog/<slug:slug>/", public_views.blog_detail_view, name="blog_detail"),
    path("sitemap.xml", public_views.sitemap_view, name="ea_sitemap"),
    path("about/", public_views.about_view, name="about"),
    
    # Programmatic SEO Directory Routes
    path("publications/<slug:slug>/", public_views.programmatic_seo_view, {"category": "publications"}, name="seo_publication"),
    path("forms/<slug:slug>/", public_views.programmatic_seo_view, {"category": "forms"}, name="seo_form"),
    path("glossary/<slug:slug>/", public_views.programmatic_seo_view, {"category": "glossary"}, name="seo_glossary"),
    path("faqs/<slug:slug>/", public_views.programmatic_seo_view, {"category": "faqs"}, name="seo_faq"),
    path("salary/<slug:slug>/", public_views.programmatic_seo_view, {"category": "salary"}, name="seo_salary"),
    path("state/<slug:slug>/", public_views.programmatic_seo_view, {"category": "state"}, name="seo_state"),
    path("country/<slug:slug>/", public_views.programmatic_seo_view, {"category": "country"}, name="seo_country"),
    
    # Gated Student Portal Pages
    path("portal/", views.ea_home, name="ea_home"),
    path("portal/part/<int:part_number>/study/", views.part_study, name="part_study"),
    path("portal/part/<int:part_number>/practice/start/", views.start_practice, name="start_practice"),
    path("practice/<int:session_id>/", views.practice_question, name="practice_question"),
    path("practice/<int:session_id>/submit/", views.practice_submit_answer, name="practice_submit_answer"),
    path("part/<int:part_number>/exam/start/", views.start_exam_simulation, name="start_exam_simulation"),
    path("exam/<int:session_id>/", views.exam_interface, name="exam_interface"),
    path("exam/<int:session_id>/submit-answer/", views.exam_submit_answer, name="exam_submit_answer"),
    path("exam/<int:session_id>/toggle-flag/", views.exam_toggle_flag, name="exam_toggle_flag"),
    path("exam/<int:session_id>/finish/", views.exam_finish, name="exam_finish"),
    path("exam/<int:session_id>/get-question/", views.exam_get_question, name="exam_get_question"),
    path("session/<int:session_id>/results/", views.session_results, name="session_results"),
    path("history/", views.exam_history, name="exam_history"),
    path("part/<int:part_number>/unlock/", views.unlock_part, name="unlock_part"),
    path("ajax/topics/<int:domain_id>/", views.get_topics_for_domain, name="get_topics_for_domain"),
    path("ajax/topics/", views.get_topics_for_domains, name="get_topics_for_domains"),
    path("ajax/mcq-counts/", views.get_mcq_counts, name="get_mcq_counts"),
    path("ajax/practice-available-count/", views.get_practice_available_count, name="practice_available_count"),
    path("ajax/add-note/", views.add_question_note, name="add_question_note"),
    path("ajax/toggle-topic-read/", views.toggle_topic_read_status, name="toggle_topic_read_status"),
]
