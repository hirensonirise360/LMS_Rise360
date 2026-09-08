"""Management command to seed EA exam domain taxonomy and sample MCQs."""
from django.core.management.base import BaseCommand
from ea_exam.models import EAPart, EADomain, EATopic, EAQuestion


TAXONOMY = {
    1: {
        "name": "Individuals",
        "domains": [
            ("Individual Income Tax Return", 17.5, ["Filing Requirements", "Filing Status", "Dependents"]),
            ("Income & Assets", 22.5, ["Gross Income", "Wages & Salary", "Interest & Dividends", "Capital Gains"]),
            ("Deductions & Credits", 17.5, ["Standard Deduction", "Itemized Deductions", "Education Credits", "Child Tax Credit"]),
            ("Taxation", 15.0, ["Tax Computation", "AMT", "Self-Employment Tax"]),
            ("Retirement Plans", 10.0, ["IRA Contributions", "IRA Distributions", "401k Rules"]),
            ("SE Tax / Other Taxes", 5.5, ["Self-Employment", "NIIT", "Additional Medicare Tax"]),
            ("Filing Status / Dependents", 12.0, ["Qualifying Child", "Qualifying Relative", "HOH"]),
        ],
    },
    2: {
        "name": "Businesses",
        "domains": [
            ("Business Entities", 27.5, ["Sole Proprietorship", "Partnerships", "S-Corps", "C-Corps", "LLCs"]),
            ("Business Income & Deductions", 25.0, ["Ordinary Deductions", "Depreciation", "Section 179", "Bonus Depreciation"]),
            ("Business Tax Credits", 12.5, ["General Business Credit", "Work Opportunity Credit"]),
            ("Accounting Methods", 17.5, ["Cash Method", "Accrual Method", "Inventory"]),
            ("Compensation & Benefits", 7.5, ["Payroll Taxes", "Fringe Benefits"]),
            ("Retirement Plans – Business", 7.5, ["SEP", "SIMPLE", "Defined Benefit"]),
            ("Other Business Taxes", 2.5, ["Excise Tax", "Environmental Tax"]),
        ],
    },
    3: {
        "name": "Representation, Practices & Procedures",
        "domains": [
            ("Practices & Procedures", 25.0, ["Power of Attorney", "Practitioner Responsibilities"]),
            ("Representation", 24.0, ["Appeals Process", "Collection Alternatives", "Audit Representation"]),
            ("Specific Areas of Representation", 19.0, ["Liens & Levies", "Innocent Spouse", "Installment Agreements"]),
            ("Filing Obligations", 18.0, ["Return Preparer Rules", "Penalties", "Extensions"]),
            ("Circular 230", 14.0, ["Standards of Practice", "Sanctions", "OPR Oversight"]),
        ],
    },
}

# Sample MCQs — Part 1
QUESTIONS_P1 = [
    {
        "domain": "Individual Income Tax Return", "topic": "Filing Requirements",
        "text": "What is the standard deduction for a single filer under age 65 for the 2023 tax year?",
        "difficulty": "easy", "irs_ref": "Pub 501",
        "choices": [
            ("$12,950", False, "That was the 2022 amount."),
            ("$13,850", True, "The 2023 standard deduction for single filers is $13,850."),
            ("$14,600", False, "That is the 2024 amount."),
            ("$11,000", False, "This is below the correct amount."),
        ],
        "explanation": "For 2023, the standard deduction for single taxpayers is $13,850 per IRS Publication 501.",
    },
    {
        "domain": "Income & Assets", "topic": "Gross Income",
        "text": "Which of the following is NOT included in gross income?",
        "difficulty": "medium", "irs_ref": "Pub 525",
        "choices": [
            ("Wages from employment", False, "Wages are always includible in gross income."),
            ("Life insurance proceeds received upon death of insured", True, "Life insurance death benefits are excluded from gross income under IRC §101."),
            ("Gambling winnings", False, "Gambling winnings must be included in gross income."),
            ("Alimony received under pre-2019 agreements", False, "Alimony under pre-2019 agreements is taxable income."),
        ],
        "explanation": "Life insurance death benefits are excluded from gross income under IRC § 101(a). Reference: Pub 525.",
    },
    {
        "domain": "Deductions & Credits", "topic": "Child Tax Credit",
        "text": "For 2023, what is the maximum Child Tax Credit per qualifying child?",
        "difficulty": "easy", "irs_ref": "Pub 972",
        "choices": [
            ("$1,000", False, "This was the pre-2018 amount."),
            ("$1,500", False, "Partially correct but not the maximum."),
            ("$2,000", True, "The Child Tax Credit is $2,000 per qualifying child for 2023."),
            ("$3,600", False, "The $3,600 was the enhanced 2021 amount."),
        ],
        "explanation": "The Child Tax Credit is $2,000 per qualifying child for tax year 2023. Income phase-outs apply.",
    },
    {
        "domain": "Taxation", "topic": "Self-Employment Tax",
        "text": "Self-employment tax is equivalent to which of the following?",
        "difficulty": "medium", "irs_ref": "Pub 334",
        "choices": [
            ("Employee's share of FICA only", False, "SE tax covers both employee and employer shares."),
            ("Employer's share of FICA only", False, "SE tax covers both shares combined."),
            ("Both employee and employer shares of Social Security and Medicare taxes", True, "Self-employed individuals pay both the employee (7.65%) and employer (7.65%) portions for a total of 15.3%."),
            ("Only Medicare tax", False, "SE tax includes both Social Security and Medicare."),
        ],
        "explanation": "Self-employed individuals must pay 15.3% SE tax (12.4% SS + 2.9% Medicare) because they bear both the employee and employer portions. Reference: Pub 334.",
    },
    {
        "domain": "Retirement Plans", "topic": "IRA Contributions",
        "text": "For 2023, what is the maximum annual contribution to a Traditional IRA for someone under age 50?",
        "difficulty": "easy", "irs_ref": "Pub 590-A",
        "choices": [
            ("$5,500", False, "This was the limit before 2019."),
            ("$6,000", False, "This was the 2022 limit."),
            ("$6,500", True, "The 2023 IRA contribution limit is $6,500 for those under 50."),
            ("$7,500", False, "The $7,500 is the catch-up limit for those 50 and older."),
        ],
        "explanation": "For 2023, the contribution limit for Traditional and Roth IRAs is $6,500 for taxpayers under 50. Reference: Pub 590-A.",
    },
    {
        "domain": "Income & Assets", "topic": "Capital Gains",
        "text": "What holding period converts a capital gain from short-term to long-term?",
        "difficulty": "easy", "irs_ref": "Pub 550",
        "choices": [
            ("6 months", False, "6 months is not sufficient for long-term treatment."),
            ("More than 12 months", True, "Assets held more than one year receive long-term capital gain treatment."),
            ("Exactly 12 months", False, "The asset must be held MORE than 12 months."),
            ("18 months", False, "18 months qualifies but is not the threshold."),
        ],
        "explanation": "A capital asset must be held for MORE than 12 months (one year) to receive long-term treatment. Reference: Pub 550.",
    },
    {
        "domain": "Individual Income Tax Return", "topic": "Filing Status",
        "text": "A taxpayer who is unmarried and paid more than half the cost of keeping a home for a qualifying person may file as:",
        "difficulty": "medium", "irs_ref": "Pub 501",
        "choices": [
            ("Single", False, "Single is available but not the most favorable status here."),
            ("Married Filing Separately", False, "The taxpayer must be unmarried."),
            ("Head of Household", True, "Head of Household applies to unmarried taxpayers who paid more than half the home costs for a qualifying person."),
            ("Qualifying Surviving Spouse", False, "QSS requires a dependent child and recently deceased spouse."),
        ],
        "explanation": "Head of Household is available to unmarried taxpayers who paid over half the cost of a home for a qualifying person. Reference: Pub 501.",
    },
    {
        "domain": "Deductions & Credits", "topic": "Education Credits",
        "text": "Which education credit is available for the first four years of post-secondary education?",
        "difficulty": "medium", "irs_ref": "Pub 970",
        "choices": [
            ("Lifetime Learning Credit", False, "LLC is not limited to the first 4 years."),
            ("American Opportunity Tax Credit", True, "AOTC covers the first four years of higher education."),
            ("Tuition and Fees Deduction", False, "This deduction has expired as of 2022."),
            ("Student Loan Interest Deduction", False, "This is a deduction, not a credit, and applies to interest, not tuition."),
        ],
        "explanation": "The AOTC is worth up to $2,500 and applies for the first four years of post-secondary education. Reference: Pub 970.",
    },
    {
        "domain": "SE Tax / Other Taxes", "topic": "NIIT",
        "text": "The Net Investment Income Tax (NIIT) rate is:",
        "difficulty": "easy", "irs_ref": "Pub 550",
        "choices": [
            ("0.9%", False, "0.9% is the Additional Medicare Tax, not NIIT."),
            ("2.9%", False, "2.9% is the standard Medicare rate."),
            ("3.8%", True, "NIIT is 3.8% on lesser of net investment income or MAGI above threshold."),
            ("5.0%", False, "5.0% is not a federal NIIT rate."),
        ],
        "explanation": "NIIT is 3.8% applied to the lesser of net investment income or the excess of MAGI over certain thresholds. Reference: Pub 550.",
    },
    {
        "domain": "Individual Income Tax Return", "topic": "Dependents",
        "text": "Which test does NOT apply to the qualifying child dependency test?",
        "difficulty": "hard", "irs_ref": "Pub 501",
        "choices": [
            ("Age test", False, "Age test is required for qualifying child."),
            ("Residency test", False, "Residency test is required."),
            ("Support test", True, "For qualifying child, parents do NOT need to provide more than half the child's support (unlike qualifying relative)."),
            ("Relationship test", False, "Relationship test is required."),
        ],
        "explanation": "The support test does not apply to a qualifying CHILD (it applies only to qualifying relative). For QC, the child must not provide more than half their own support. Reference: Pub 501.",
    },
]

# Sample MCQs — Part 2
QUESTIONS_P2 = [
    {
        "domain": "Business Entities", "topic": "Sole Proprietorship",
        "text": "A sole proprietor reports business income and expenses on which form?",
        "difficulty": "easy", "irs_ref": "Pub 334",
        "choices": [
            ("Form 1065", False, "Form 1065 is used by partnerships."),
            ("Schedule C (Form 1040)", True, "Sole proprietors file Schedule C to report business income/loss."),
            ("Form 1120", False, "Form 1120 is used by C-corporations."),
            ("Schedule E (Form 1040)", False, "Schedule E is used for rental, S-corp, and partnership income."),
        ],
        "explanation": "Sole proprietors report business profit or loss on Schedule C and attach it to Form 1040. Reference: Pub 334.",
    },
    {
        "domain": "Business Income & Deductions", "topic": "Section 179",
        "text": "Section 179 allows a taxpayer to:",
        "difficulty": "medium", "irs_ref": "Pub 946",
        "choices": [
            ("Deduct the full cost of qualified property in the year it is placed in service", True, "Section 179 allows immediate expensing of qualifying assets up to the annual limit."),
            ("Defer income to future years", False, "Section 179 is a deduction, not a deferral method."),
            ("Claim a credit equal to the cost of the asset", False, "Section 179 is a deduction, not a credit."),
            ("Depreciate assets over 3 years", False, "Section 179 accelerates to current-year deduction, not 3-year."),
        ],
        "explanation": "Section 179 lets businesses immediately expense the cost of eligible business property placed in service during the year, up to $1,160,000 for 2023. Reference: Pub 946.",
    },
    {
        "domain": "Accounting Methods", "topic": "Cash Method",
        "text": "Under the cash method of accounting, income is recognized when:",
        "difficulty": "easy", "irs_ref": "Pub 538",
        "choices": [
            ("Goods or services are delivered", False, "That is the accrual method."),
            ("An invoice is issued", False, "Invoice issuance is not recognition under cash method."),
            ("Cash or its equivalent is actually or constructively received", True, "Cash method recognizes income when actually or constructively received."),
            ("The contract is signed", False, "Signing a contract does not trigger income recognition."),
        ],
        "explanation": "Under cash basis accounting, income is reported when actually or constructively received, regardless of when earned. Reference: Pub 538.",
    },
    {
        "domain": "Business Tax Credits", "topic": "General Business Credit",
        "text": "The Work Opportunity Tax Credit (WOTC) incentivizes employers to hire individuals from which groups?",
        "difficulty": "medium", "irs_ref": "Form 5884 Instructions",
        "choices": [
            ("Only veterans", False, "Veterans are included but not the only group."),
            ("Only ex-felons", False, "Ex-felons are included but not the only group."),
            ("Targeted groups including veterans, recipients of public assistance, and ex-felons", True, "WOTC covers multiple targeted groups including veterans, TANF recipients, ex-felons, and others."),
            ("Any new hire during a recession", False, "WOTC targets specific defined groups, not all hires."),
        ],
        "explanation": "WOTC provides a tax credit to employers who hire individuals from defined targeted groups. Reference: Form 5884 Instructions.",
    },
    {
        "domain": "Business Entities", "topic": "S-Corps",
        "text": "An S-corporation shareholder's stock basis is important because it limits the shareholder's ability to:",
        "difficulty": "hard", "irs_ref": "Pub 589",
        "choices": [
            ("Vote at shareholder meetings", False, "Basis does not affect voting rights."),
            ("Deduct flow-through losses", True, "S-corp shareholders can only deduct losses up to their stock and debt basis."),
            ("Receive dividends", False, "S-corps do not pay dividends; they distribute earnings."),
            ("Participate in management", False, "Basis has no effect on management."),
        ],
        "explanation": "A shareholder in an S-corporation may only deduct their share of the corporation's losses to the extent of their basis in stock and any loans made to the corporation. Reference: Pub 589.",
    },
    {
        "domain": "Business Income & Deductions", "topic": "Depreciation",
        "text": "Under MACRS, what is the recovery period for most commercial real property?",
        "difficulty": "medium", "irs_ref": "Pub 946",
        "choices": [
            ("15 years", False, "15 years applies to land improvements."),
            ("27.5 years", False, "27.5 years applies to residential rental property."),
            ("39 years", True, "Nonresidential real property is depreciated over 39 years under MACRS."),
            ("50 years", False, "50 years is not a standard MACRS period."),
        ],
        "explanation": "MACRS assigns a 39-year recovery period for nonresidential (commercial) real property. Reference: Pub 946.",
    },
    {
        "domain": "Compensation & Benefits", "topic": "Fringe Benefits",
        "text": "Which of the following employer-provided benefits is generally excludable from an employee's gross income?",
        "difficulty": "medium", "irs_ref": "Pub 15-B",
        "choices": [
            ("Cash bonuses", False, "Cash is always includible in income."),
            ("Group-term life insurance up to $50,000", True, "Employer-paid group-term life insurance premiums for coverage up to $50,000 are excludable."),
            ("Personal use of company car", False, "Personal use of a company car is a taxable fringe benefit."),
            ("Gym membership paid directly to employee", False, "Direct cash reimbursements for gym memberships are generally taxable."),
        ],
        "explanation": "Employer-provided group-term life insurance coverage up to $50,000 is excluded from employee gross income. Reference: Pub 15-B.",
    },
    {
        "domain": "Retirement Plans – Business", "topic": "SEP",
        "text": "The maximum SEP-IRA contribution for a self-employed individual for 2023 is limited to the lesser of 25% of compensation or:",
        "difficulty": "medium", "irs_ref": "Pub 560",
        "choices": [
            ("$61,000", False, "That was the 2022 limit."),
            ("$66,000", True, "The 2023 SEP contribution limit is the lesser of 25% of compensation or $66,000."),
            ("$58,000", False, "That was an earlier limit."),
            ("$73,500", False, "That is the 401(k) catch-up limit for 2023."),
        ],
        "explanation": "For 2023, SEP-IRA contributions are limited to the lesser of 25% of compensation or $66,000. Reference: Pub 560.",
    },
    {
        "domain": "Business Entities", "topic": "Partnerships",
        "text": "How is partnership income taxed?",
        "difficulty": "easy", "irs_ref": "Pub 541",
        "choices": [
            ("At the partnership level at corporate tax rates", False, "Partnerships are pass-through entities."),
            ("It passes through to each partner and is reported on their individual returns", True, "Partnerships file Form 1065 but income/loss passes through to partners via Schedule K-1."),
            ("Only when distributed to partners", False, "Partners are taxed on their allocable share, not just distributions."),
            ("At a flat 21% rate", False, "21% is the corporate rate, not applicable to partnerships."),
        ],
        "explanation": "A partnership is a pass-through entity. It files Form 1065, and each partner receives a Schedule K-1 reporting their share of income, deductions, and credits. Reference: Pub 541.",
    },
    {
        "domain": "Business Income & Deductions", "topic": "Bonus Depreciation",
        "text": "For property placed in service in 2023, what is the bonus depreciation percentage?",
        "difficulty": "medium", "irs_ref": "Pub 946",
        "choices": [
            ("100%", False, "100% bonus depreciation applied through 2022."),
            ("80%", True, "Bonus depreciation phases down to 80% for property placed in service in 2023."),
            ("60%", False, "60% applies to 2024."),
            ("50%", False, "50% was the rate in prior phase-down years."),
        ],
        "explanation": "The Tax Cuts and Jobs Act 100% bonus depreciation phases down: 80% for 2023, 60% for 2024, 40% for 2025, 20% for 2026. Reference: Pub 946.",
    },
]

# Sample MCQs — Part 3
QUESTIONS_P3 = [
    {
        "domain": "Practices & Procedures", "topic": "Power of Attorney",
        "text": "Which form is used to authorize a representative to act on behalf of a taxpayer before the IRS?",
        "difficulty": "easy", "irs_ref": "Pub 947",
        "choices": [
            ("Form 2848", True, "Form 2848 (Power of Attorney and Declaration of Representative) authorizes a representative before the IRS."),
            ("Form 8821", False, "Form 8821 is a Tax Information Authorization giving access to tax info, not full representation."),
            ("Form 1099", False, "Form 1099 is an information return, not a POA."),
            ("Form 4868", False, "Form 4868 is for filing extensions."),
        ],
        "explanation": "Form 2848 grants an individual (EA, CPA, attorney) power of attorney to represent a taxpayer before the IRS. Reference: Pub 947.",
    },
    {
        "domain": "Circular 230", "topic": "Standards of Practice",
        "text": "Under Circular 230, an Enrolled Agent must NOT:",
        "difficulty": "medium", "irs_ref": "Circular 230 §10.22",
        "choices": [
            ("Advise a client about the tax consequences of a transaction", False, "This is a core EA function."),
            ("Charge a contingent fee for preparing an original tax return", True, "Circular 230 prohibits contingent fees for original tax return preparation."),
            ("Represent a client in an IRS audit", False, "Representation is a key EA function."),
            ("Obtain a client's signature on a power of attorney", False, "This is normal EA practice."),
        ],
        "explanation": "Circular 230 §10.27 prohibits practitioners from charging contingent fees for preparation of original tax returns. Reference: Circular 230.",
    },
    {
        "domain": "Representation", "topic": "Collection Alternatives",
        "text": "An Offer in Compromise (OIC) allows a taxpayer to:",
        "difficulty": "medium", "irs_ref": "Pub 594",
        "choices": [
            ("Delay tax payments for up to 10 years", False, "OIC is not a delay—it is a settlement."),
            ("Settle a tax debt for less than the full amount owed", True, "An OIC allows taxpayers to settle their tax liability for less than the full amount if they qualify."),
            ("Eliminate all penalties automatically", False, "OIC does not automatically eliminate penalties."),
            ("Convert tax debt to a business loan", False, "OIC is a settlement program, not a loan conversion."),
        ],
        "explanation": "An Offer in Compromise allows eligible taxpayers to resolve their tax debt for less than the full amount owed based on ability to pay, income, expenses, and asset equity. Reference: Pub 594.",
    },
    {
        "domain": "Filing Obligations", "topic": "Penalties",
        "text": "The failure-to-file penalty for a late return (without fraud) is generally:",
        "difficulty": "medium", "irs_ref": "Pub 17",
        "choices": [
            ("0.5% per month up to 25%", False, "0.5%/month is the failure-to-PAY penalty."),
            ("5% per month up to 25% of unpaid tax", True, "The failure-to-file penalty is 5% per month (or part of a month) on the unpaid tax, up to a maximum of 25%."),
            ("10% flat penalty", False, "10% flat is not the standard FTF penalty."),
            ("1% per month up to 12%", False, "This matches neither FTF nor FTP penalty rates."),
        ],
        "explanation": "The failure-to-file penalty is 5% per month of unpaid tax, up to 25%. If both FTF and FTP apply, the FTP rate is subtracted from FTF. Reference: Pub 17.",
    },
    {
        "domain": "Specific Areas of Representation", "topic": "Installment Agreements",
        "text": "Which installment agreement type allows the IRS to automatically approve if the taxpayer owes $10,000 or less?",
        "difficulty": "hard", "irs_ref": "Pub 594",
        "choices": [
            ("Partial Pay Installment Agreement", False, "PPIA requires full financial disclosure."),
            ("Guaranteed Installment Agreement", True, "The IRS must accept a guaranteed installment agreement if total tax owed is $10,000 or less and conditions are met."),
            ("Streamlined Installment Agreement", False, "Streamlined applies to balances up to $50,000."),
            ("In-Business Trust Fund Express Agreement", False, "IBTF Express is for business payroll taxes."),
        ],
        "explanation": "Under a Guaranteed Installment Agreement, the IRS is required to accept your payment plan if you owe $10,000 or less and meet certain conditions. Reference: Pub 594.",
    },
    {
        "domain": "Representation", "topic": "Appeals Process",
        "text": "After receiving a 30-day letter, a taxpayer who disagrees with IRS proposed changes should:",
        "difficulty": "medium", "irs_ref": "Pub 5",
        "choices": [
            ("File immediately in Tax Court", False, "Tax Court requires a 90-day notice of deficiency first."),
            ("Request a conference with the IRS Independent Office of Appeals", True, "A 30-day letter allows the taxpayer to request a conference with Appeals before the IRS issues a formal notice of deficiency."),
            ("Ignore it—it has no legal effect", False, "Ignoring a 30-day letter will lead to a 90-day notice of deficiency."),
            ("Pay in full immediately to avoid further action", False, "The taxpayer has the right to dispute before paying."),
        ],
        "explanation": "A 30-day letter invites the taxpayer to request an appeals conference. This is the first step in disputing IRS proposed changes. Reference: Pub 5.",
    },
    {
        "domain": "Circular 230", "topic": "Sanctions",
        "text": "Which sanction under Circular 230 permanently bars a practitioner from practicing before the IRS?",
        "difficulty": "hard", "irs_ref": "Circular 230 §10.50",
        "choices": [
            ("Censure", False, "Censure is a public reprimand but does not revoke practice rights."),
            ("Suspension", False, "Suspension is temporary."),
            ("Disbarment", True, "Disbarment permanently prohibits a practitioner from practicing before the IRS."),
            ("Monetary penalty", False, "Monetary penalty is a fine, not a bar to practice."),
        ],
        "explanation": "Under Circular 230 §10.50, disbarment is the most severe sanction and permanently prevents a practitioner from practicing before the IRS. Reference: Circular 230.",
    },
    {
        "domain": "Practices & Procedures", "topic": "Practitioner Responsibilities",
        "text": "An enrolled agent discovers that a client's prior year return contains an error. What must the EA do?",
        "difficulty": "medium", "irs_ref": "Circular 230 §10.21",
        "choices": [
            ("Immediately file an amended return without the client's knowledge", False, "The EA cannot act without client authorization."),
            ("Promptly advise the client of the noncompliance and the consequences", True, "Circular 230 §10.21 requires EAs to promptly advise clients of noncompliance and consequences, but cannot file amended returns without authorization."),
            ("Report the error directly to the IRS", False, "EAs are not required to report client errors directly to the IRS."),
            ("Ignore it if the error is minor", False, "All errors must be disclosed to the client."),
        ],
        "explanation": "Circular 230 §10.21 requires a practitioner who knows of a client's noncompliance to promptly advise the client of the consequences. Reference: Circular 230.",
    },
    {
        "domain": "Filing Obligations", "topic": "Return Preparer Rules",
        "text": "A tax return preparer who willfully attempts to understate tax liability may be subject to a penalty of:",
        "difficulty": "hard", "irs_ref": "IRC §6694",
        "choices": [
            ("The greater of $1,000 or 50% of the income derived", True, "IRC §6694(b) imposes a penalty of the greater of $1,000 or 50% of the income derived for willful understatement."),
            ("$500 per return", False, "$500 applies to the lesser, non-willful understatement."),
            ("$250 per return", False, "This is not the applicable penalty."),
            ("10% of the understated tax", False, "The penalty is based on preparer income, not understated tax."),
        ],
        "explanation": "For willful or fraudulent understatement of liability, IRC §6694(b) applies: the greater of $1,000 or 50% of income derived from the return. Reference: IRC §6694.",
    },
    {
        "domain": "Specific Areas of Representation", "topic": "Innocent Spouse",
        "text": "Which form is filed to request innocent spouse relief?",
        "difficulty": "easy", "irs_ref": "Pub 971",
        "choices": [
            ("Form 8857", True, "Form 8857 (Request for Innocent Spouse Relief) is used to request relief from joint liability."),
            ("Form 2848", False, "Form 2848 is Power of Attorney."),
            ("Form 12153", False, "Form 12153 is a Request for a Collection Due Process Hearing."),
            ("Form 9465", False, "Form 9465 is used to request an installment agreement."),
        ],
        "explanation": "Form 8857 is used to apply for innocent spouse relief, separation of liability, or equitable relief. Reference: Pub 971.",
    },
]


class Command(BaseCommand):
    help = "Seed EA exam taxonomy (Parts, Domains, Topics) and sample MCQs"

    def handle(self, *args, **options):
        self.stdout.write("Seeding EA taxonomy...")
        self._seed_taxonomy()
        self.stdout.write("Seeding sample questions...")
        self._seed_questions()
        self.stdout.write(self.style.SUCCESS("Done! EA exam data seeded successfully."))

    def _seed_taxonomy(self):
        for part_num, part_data in TAXONOMY.items():
            part, _ = EAPart.objects.get_or_create(
                number=part_num,
                defaults={
                    "name": part_data["name"],
                    "total_questions": 100,
                    "time_limit_minutes": 210,
                }
            )
            for order, (domain_name, weight, topics) in enumerate(part_data["domains"]):
                domain, _ = EADomain.objects.get_or_create(
                    part=part, name=domain_name,
                    defaults={"prometric_weight": weight, "order": order}
                )
                for t_order, topic_name in enumerate(topics):
                    EATopic.objects.get_or_create(
                        domain=domain, name=topic_name,
                        defaults={"order": t_order}
                    )

    def _seed_questions(self):
        question_sets = [
            (1, QUESTIONS_P1),
            (2, QUESTIONS_P2),
            (3, QUESTIONS_P3),
        ]
        for part_num, questions in question_sets:
            part = EAPart.objects.get(number=part_num)
            for q_data in questions:
                domain = EADomain.objects.filter(part=part, name=q_data["domain"]).first()
                if not domain:
                    continue
                topic = EATopic.objects.filter(domain=domain, name=q_data["topic"]).first()

                defaults = {
                    "part": part,
                    "domain": domain,
                    "topic": topic,
                    "explanation": q_data["explanation"],
                    "difficulty": q_data["difficulty"],
                    "irs_pub_ref": q_data["irs_ref"],
                    "status": "active",
                }
                
                choices_data = q_data["choices"]
                if len(choices_data) > 0:
                    defaults["choice_1"] = choices_data[0][0]
                    defaults["choice_1_correct"] = choices_data[0][1]
                if len(choices_data) > 1:
                    defaults["choice_2"] = choices_data[1][0]
                    defaults["choice_2_correct"] = choices_data[1][1]
                if len(choices_data) > 2:
                    defaults["choice_3"] = choices_data[2][0]
                    defaults["choice_3_correct"] = choices_data[2][1]
                if len(choices_data) > 3:
                    defaults["choice_4"] = choices_data[3][0]
                    defaults["choice_4_correct"] = choices_data[3][1]

                q, created = EAQuestion.objects.get_or_create(
                    question_text=q_data["text"],
                    defaults=defaults
                )
        self.stdout.write(f"Created {EAQuestion.objects.count()} questions total.")
