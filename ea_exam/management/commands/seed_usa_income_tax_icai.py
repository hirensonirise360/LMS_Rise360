from django.core.management.base import BaseCommand
from django.db.models import Max
from ea_exam.models import EAPart, EADomain, EATopic


PLAYLIST_TOPICS = [
    {
        "order": 1,
        "name": "Day 1 : Part 1 : OVERVIEW US TAXATION AND RESIDENCY CLASSIFICATION 1",
        "video_url": "https://www.youtube.com/watch?v=NH8K5BLM_PM",
    },
    {
        "order": 2,
        "name": "Day 1 part 2 : OVERVIEW US TAXATION AND RESIDENCY CLASSIFICATION 2",
        "video_url": "https://www.youtube.com/watch?v=_GF6-1kJz6E",
    },
    {
        "order": 3,
        "name": "Day 2 : Part 1 : OVERVIEW US TAXATION AND RESIDENCY CLASSIFICATION 3",
        "video_url": "https://www.youtube.com/watch?v=8ZTnIzafm9U",
    },
    {
        "order": 4,
        "name": "Day 2 : Part 2 : OVERVIEW US TAXATION AND RESIDENCY CLASSIFICATION 4",
        "video_url": "https://www.youtube.com/watch?v=CUKZqcVjuV4",
    },
    {
        "order": 5,
        "name": "Day 3 : Part 1 : INDIVIDUAL TAXATION 1",
        "video_url": "https://www.youtube.com/watch?v=Ikia2rFWlng",
    },
    {
        "order": 6,
        "name": "Day 3 : Part 2 : INDIVIDUAL TAXATION 2",
        "video_url": "https://www.youtube.com/watch?v=b-qrPDQZDWc",
    },
    {
        "order": 7,
        "name": "Day 4 : ITEMIZED DEDUCTIONS",
        "video_url": "https://www.youtube.com/watch?v=vHgYD4_Yu_Y",
    },
    {
        "order": 8,
        "name": "Day 4 : SELF EMPLOYMENT TAX & IRA",
        "video_url": "https://www.youtube.com/watch?v=S1a4IqxOdbg",
    },
    {
        "order": 9,
        "name": "Day 5 AMT, HSA, NII and SSB",
        "video_url": "https://www.youtube.com/watch?v=AMVtTyHgHWg",
    },
    {
        "order": 10,
        "name": "DAY 6 : recap Individual Taxation day 4",
        "video_url": "https://www.youtube.com/watch?v=UXlca_YvVPU",
    },
    {
        "order": 11,
        "name": "Day 6 : Tax credits",
        "video_url": "https://www.youtube.com/watch?v=U8YtyW_hBVA",
    },
    {
        "order": 12,
        "name": "Day 7 : Business Entity Taxation 1",
        "video_url": "https://www.youtube.com/watch?v=VA85aoWvQmM",
    },
    {
        "order": 13,
        "name": "Day 7 : Part 2 : Business Entity Taxation 2",
        "video_url": "https://www.youtube.com/watch?v=_8c8RKp5_8g",
    },
    {
        "order": 14,
        "name": "Day 7 : Part 3 : Case studies",
        "video_url": "https://www.youtube.com/watch?v=fm2_QWTsXrI",
    },
    {
        "order": 15,
        "name": "Day 8 Business Entity Taxation",
        "video_url": "https://www.youtube.com/watch?v=TAMXZdsTlV0",
    },
    {
        "order": 16,
        "name": "Day 9 International Taxation & Cross Border Issues(W-8BEN,W-8ECI,1042-S, 8833, FIRPTA and FDAP & ECI",
        "video_url": "https://www.youtube.com/watch?v=I6phQGIBkEM",
    },
    {
        "order": 17,
        "name": "Day 10 Form 5471, 5472, 8865, 8621,CFC, P'ship, and PFIC, FTC, Passive Income, FATCA, trusts, gifts",
        "video_url": "https://www.youtube.com/watch?v=jygiYMExBeE",
    },
    {
        "order": 18,
        "name": "Day 11 US- India Tax Treaty (DTAA, Key treaty articles: Dual Residency & Tie-breaker Rules, PE)",
        "video_url": "https://www.youtube.com/watch?v=BSN-ZaHygfY",
    },
    {
        "order": 19,
        "name": "Day 12 US- India Tax Treaty (Bus. Profits, Royalty, Fees -Tech. Services, Form 1116/1118",
        "video_url": "https://www.youtube.com/watch?v=bTwaoreXl8Q",
    },
    {
        "order": 20,
        "name": "Day 13  IRS Procedures, Ethics & Representations",
        "video_url": "https://www.youtube.com/watch?v=Kn6dMXoQt20",
    },
    {
        "order": 21,
        "name": "Day 14  IRS Procedures, Ethics & Representations",
        "video_url": "https://www.youtube.com/watch?v=PulnJRTVKwk",
    },
    {
        "order": 22,
        "name": "Day 15 Reporting, Withholding & Specialized Forms-(1099 MISC, NEC, INT, DIV, K)1098, W-2)&Penalties",
        "video_url": "https://www.youtube.com/watch?v=HzpdySSjszA",
    },
    {
        "order": 23,
        "name": "Day 16 Contractor vs. Employee and Common Errors & IRS Correspondence and FATCA, FATF, FBAR and 8938",
        "video_url": "https://www.youtube.com/watch?v=c7lepHlB-Zk",
    },
    {
        "order": 24,
        "name": "Day 17 Overview of software - Drake, Lacerte, Pro Series, TurboTax",
        "video_url": "https://www.youtube.com/watch?v=XAHdYsw5naI",
    },
    {
        "order": 25,
        "name": "Day 18 Sample Return Preparation (1040/1040SR/1040NR, 1120/1120S, Form 1065, K-1)",
        "video_url": "https://www.youtube.com/watch?v=OyNcHGd72xw",
    },
    {
        "order": 26,
        "name": "Day 19 Reporting, Withholding & Specialized Forms",
        "video_url": "https://www.youtube.com/watch?v=ZH_fkiZQQw4",
    },
    {
        "order": 27,
        "name": "Day 20 Case Studies : Dual Status taxpayer, Indian Freelancer, Indian Partner in U.S. LLC.",
        "video_url": "https://www.youtube.com/watch?v=g5GyQO8Rau0",
    },
    {
        "order": 28,
        "name": "Day 21 Form 1040, Adjustment and IRA",
        "video_url": "https://www.youtube.com/watch?v=uBlb3heoCHs",
    },
]


class Command(BaseCommand):
    help = "Create 'USA Income Tax ICAI' domain under USA Taxation module and populate 28 topics with YouTube video URLs."

    def handle(self, *args, **options):
        # 1. Find USA Taxation module / EAPart
        part = EAPart.objects.filter(name__icontains="USA Taxation").first()
        if not part:
            part = EAPart.objects.filter(number=5).first()
        
        if not part:
            self.stdout.write(self.style.ERROR("USA Taxation module (EAPart) not found."))
            return

        self.stdout.write(f"Found Module: {part.name} (Part #{part.number})")

        # 2. Get or create Domain "USA Income Tax ICAI"
        max_order = EADomain.objects.filter(part=part).aggregate(Max('order'))['order__max'] or 0
        domain, created = EADomain.objects.get_or_create(
            part=part,
            name="USA Income Tax ICAI",
            defaults={"order": max_order + 1}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Domain: '{domain.name}' with order {domain.order}"))
        else:
            self.stdout.write(f"Domain '{domain.name}' already exists (order {domain.order}). Updating topics...")

        # 3. Create or update the 28 topics
        created_count = 0
        updated_count = 0

        for item in PLAYLIST_TOPICS:
            topic, t_created = EATopic.objects.update_or_create(
                domain=domain,
                order=item["order"],
                defaults={
                    "name": item["name"],
                    "video_external_url": item["video_url"],
                }
            )
            if t_created:
                created_count += 1
                self.stdout.write(f"  + Created Topic {topic.order}: {topic.name}")
            else:
                updated_count += 1
                self.stdout.write(f"  ~ Updated Topic {topic.order}: {topic.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully processed {len(PLAYLIST_TOPICS)} topics for domain '{domain.name}' (Created: {created_count}, Updated: {updated_count})."
            )
        )
