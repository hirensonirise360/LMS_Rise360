import random
from datetime import date

from django.core.management.base import BaseCommand
from ea_exam.models import EAPart, EADomain
from ea_content.models import Flashcard, EANote


class Command(BaseCommand):
    help = "Seeds the database with sample EA Phase 3 content (Flashcards, IRS Pubs, Notes)."

    def handle(self, *args, **options):
        self.stdout.write("Started seeding EA Phase 3 Content Data...")

        if not EAPart.objects.exists():
            self.stdout.write(self.style.ERROR("EAPart models not found. Please run 'seed_ea_data' first."))
            return

        part1 = EAPart.objects.get(number=1)
        part2 = EAPart.objects.get(number=2)
        part3 = EAPart.objects.get(number=3)



        # 3. Seed Flashcards
        flashcards_data = [
            # Part 1
            (part1, "Qualifying Child Age Limit", "Must be under age 19 at the end of the year, OR under age 24 if a full-time student for at least 5 months. (No age limit if permanently and totally disabled).", "Individual Income Tax Return", "easy"),
            (part1, "Standard Deduction - Single (2023/2024)", "Single filers standard deduction is generally adjusted annually. It is a set amount that reduces taxable income.", "Adjustments & Deductions", "easy"),
            (part1, "Capital Loss Deduction Limit", "Net capital losses can be deducted up to $3,000 per year against ordinary income ($1,500 if Married Filing Separately).", "Capital Gains", "average"),
            (part1, "Gift Tax Annual Exclusion", "The annual exclusion allows a donor to give up to a specific amount per donee per year without filing a gift tax return (e.g., $17,000 for 2023, $18,000 for 2024).", "Specialized returns and Topics", "average"),
            (part1, "Section 121 Exclusion (Sale of Home)", "Exclude up to $250,000 ($500,000 MFJ) of gain on the sale of a primary residence if owned and lived in for 2 of the last 5 years.", "Calculating Tax & Tax Credits", "hard"),
            
            # Part 2
            (part2, "S Corporation - Eligible Shareholders", "Must be US citizens or residents, certain trusts, and estates. Cannot be C-corps, partnerships, or non-resident aliens. Max 100 shareholders (families count as 1).", "S Corps", "average"),
            (part2, "Section 179 Deduction", "Allows businesses to deduct the full purchase price of qualifying equipment and/or software purchased or financed during the tax year, up to a limit.", "Assets and Depreciation", "easy"),
            (part2, "Partnership - Basis vs. At-Risk", "Partner losses are limited first by their adjusted basis in the partnership, then by their 'at-risk' amount, then by passive activity rules.", "Sole Proprietorships and partnerships", "hard"),
            (part2, "MACRS - 5-Year Property", "Includes automobiles, taxis, buses, light/heavy trucks, computers, and peripheral equipment.", "Assets and Depreciation", "easy"),
            (part2, "Corporate Dividend Received Deduction (DRD)", "If ownership is < 20%, DRD is 50%. If ownership is 20% to just under 80%, DRD is 65%. If >= 80%, DRD is 100%.", "C Corps", "hard"),
            
            # Part 3
            (part3, "Circular 230 - Due Diligence", "A practitioner must exercise due diligence in preparing or assisting in the preparation of tax returns and other documents relating to IRS matters.", "Practices and Procedures", "easy"),
            (part3, "Statute of Limitations - Tax Assessment", "Generally 3 years from the date the return was filed (or due date if filed early). 6 years if gross income omitted is > 25%. Indefinite for fraud or failure to file.", "Tax Filing Process", "average"),
            (part3, "Form 2848", "Power of Attorney and Declaration of Representative. Allows an eligible representative (like an EA) to represent a taxpayer before the IRS.", "Representation Before the IRS 1", "easy"),
            (part3, "FOIA Request", "Freedom of Information Act. Taxpayers/representatives use this to request their administrative file or specific IRS records not available via normal transcripts.", "Representation Before the IRS 2", "average"),
            (part3, "Failure to File vs. Failure to Pay Penalty", "Failure to File: 5% per month (up to 25%). Failure to Pay: 0.5% per month (up to 25%). If both apply, the 5% FTF is reduced by the 0.5% FTP penalty (net 4.5% FTF).", "Tax Filing Process", "hard"),
        ]

        fc_created = 0
        fc_updated = 0
        for part, front, back, domain_name, difficulty in flashcards_data:
            domain_obj = EADomain.objects.filter(part=part, name__icontains=domain_name).first()
            if not domain_obj:
                domain_obj = EADomain.objects.filter(part=part).first()

            obj, created = Flashcard.objects.get_or_create(
                front=front,
                defaults={
                    "part": part, 
                    "back": back,
                    "domain": domain_obj,
                    "difficulty": difficulty,
                    "is_published": True
                }
            )
            if created:
                fc_created += 1
            else:
                obj.domain = domain_obj
                obj.difficulty = difficulty
                obj.back = back
                obj.part = part
                obj.save()
                fc_updated += 1

        if fc_created > 0:
            self.stdout.write(self.style.SUCCESS(f"Seeded {fc_created} Flashcards."))
        if fc_updated > 0:
            self.stdout.write(self.style.SUCCESS(f"Updated {fc_updated} existing Flashcards."))

        # 4. Seed an Admin Note
        if not EANote.objects.filter(title="Welcome to EA Exam Prep Notes").exists():
            EANote.objects.create(
                title="Welcome to EA Exam Prep Notes",
                part=part1,
                content="This is the official study notes repository. Here you will find summary sheets created by instructors, as well as any personal notes you create while studying.\n\nGood luck with your Enrolled Agent journey!",
                is_admin_note=True
            )
            self.stdout.write(self.style.SUCCESS("Seeded Welcome Admin Note."))

        self.stdout.write(self.style.SUCCESS("Phase 3 Content Seeding Complete!"))
