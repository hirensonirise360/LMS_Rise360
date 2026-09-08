# -*- coding: utf-8 -*-

"""
Programmatic SEO Datastore for RISE360 Institute.
This module holds structured tax datasets that generate dynamic, high-performance SEO/GEO pages.
"""

PUBLICATIONS_DATA = {
    "pub-17-individual-tax-guide": {
        "title": "IRS Publication 17 (2025) Guide: Individual Tax Rules for EA Exam",
        "meta_description": "Master IRS Publication 17 for the EA Exam Part 1. Detailed breakdown of gross income, deductions, tax credits, filing status, and standard deductions.",
        "type": "IRS Publication",
        "code": "Pub 17",
        "quick_answer": "IRS Publication 17 (Your Federal Income Tax) is the ultimate guide for individual federal income tax rules. It is the primary reference material for Part 1 of the Special Enrollment Examination (SEE).",
        "definition": "IRS Publication 17 covers the general rules for filing a federal income tax return. It explains how to determine gross income, adjust gross income, calculate standard or itemized deductions, and apply tax credits to determine the final tax liability or refund.",
        "key_facts": [
            "Filing Thresholds: Adjusted annually for inflation.",
            "Standard Deduction: Set at $15,000 for single filers and $30,000 for married filing jointly (2025 tax year projections).",
            "Itemized Deductions: Reported on Schedule A (Form 1040) for medical, taxes paid, interest, and charity.",
            "Tax Brackets: Progressive system ranging from 10% to 37% across 7 income brackets."
        ],
        "bullet_summary": [
            "Part 1 Foundation: Publication 17 comprises over 50% of the tested content on EA Exam Part 1.",
            "Income Inclusions: Wages, interest, dividends, capital gains, retirement distributions, and alimony.",
            "Above-the-Line Deductions: Educator expenses, student loan interest, and HSA contributions that reduce Adjusted Gross Income (AGI).",
            "Nonrefundable vs Refundable Credits: Nonrefundable credits reduce tax to zero, while refundable credits (like EITC) can trigger cash refunds."
        ],
        "stats": {
            "Total Pages": "130+",
            "SEE Exam Weight": "High (Part 1)",
            "Target Tax Year": "2025",
            "Core Forms Covered": "Form 1040, Schedules A, B, C, D"
        },
        "table": {
            "headers": ["Filing Status", "Standard Deduction (2024)", "Standard Deduction (2025 Est)"],
            "rows": [
                ["Single", "$14,600", "$15,000"],
                ["Married Filing Jointly", "$29,200", "$30,000"],
                ["Head of Household", "$21,900", "$22,500"],
                ["Married Filing Separately", "$14,600", "$15,000"]
            ]
        },
        "faqs": [
            {
                "q": "What is the primary purpose of IRS Publication 17?",
                "a": "It serves as the comprehensive tax guide for individuals, explaining how to file a federal income tax return, calculate taxable income, and claim deductions and credits."
            },
            {
                "q": "How heavily is Publication 17 tested on the EA Exam?",
                "a": "It is the foundational publication for EA Exam Part 1 (Individuals). Over 90% of the questions regarding individual filing status, income exclusions, and deductions are sourced directly from Pub 17 rules."
            }
        ],
        "citations": [
            {"name": "Official IRS Publication 17 Page", "url": "https://www.irs.gov/forms-pubs/about-publication-17"}
        ],
        "content": "<p>IRS Publication 17 is updated annually by the Internal Revenue Service to reflect statutory changes, inflation adjustments, and tax reform provisions. For Enrolled Agent candidates, mastering Pub 17 is non-negotiable for passing Part 1 of the SEE.</p><h3>Key Tax Concepts in Pub 17</h3><p>To pass Part 1, you must understand the distinction between inclusions in gross income and exclusions (such as municipal bond interest or life insurance proceeds). Furthermore, candidates must memorize the differences between adjustments to income (AGI deductions) and deductions from AGI (standard or itemized deductions).</p>",
        "related_topics": [
            {"name": "EA Exam Part 1 Guide", "url": "/en/ea/part/1/"},
            {"name": "Form 1040 Breakdown", "url": "/en/ea/forms/form-1040-individual-tax-return/"}
        ]
    },
    "pub-535-business-expenses": {
        "title": "IRS Publication 535: Business Expenses Guide for EA Exam Part 2",
        "meta_description": "Understand IRS Publication 535 for Business Expenses on the EA Exam. Learn what makes an expense ordinary and necessary under IRC Section 162.",
        "type": "IRS Publication",
        "code": "Pub 535",
        "quick_answer": "IRS Publication 535 details the rules for deducting business expenses. To be deductible under Internal Revenue Code Section 162, a business expense must be both ordinary and necessary.",
        "definition": "Business expenses are the costs of carrying on a trade, business, or profession. Publication 535 explains which expenses can be deducted in full, capitalized, amortized, or disallowed entirely (such as personal expenses, fines, and political contributions).",
        "key_facts": [
            "Ordinary Expense: Common and accepted in your industry.",
            "Necessary Expense: Helpful and appropriate for your trade or business.",
            "Capital Expenditures: Assets with a useful life exceeding one year must be capitalized rather than expensed.",
            "Section 179 Deduction: Allows businesses to expense the full cost of qualifying equipment in the year of purchase."
        ],
        "bullet_summary": [
            "IRC Section 162: The statutory authority governing ordinary and necessary business expenses.",
            "Disallowed Expenses: Penalties paid to governments, lobbyist fees, and personal meals are non-deductible.",
            "Business Bad Debts: Deductible only under the specific charge-off method; the reserve method is disallowed for tax.",
            "Amortization: Startup costs and organizational expenses up to $5,000 can be immediately expensed, with the remainder amortized over 180 months."
        ],
        "stats": {
            "LMS Practice Questions": "150+ Questions",
            "SEE Exam Weight": "High (Part 2)",
            "Primary IRS Section": "IRC Section 162",
            "Related Entity Schedules": "Schedule C (Form 1040), Form 1065, Form 1120"
        },
        "table": {
            "headers": ["Expense Category", "Tax Treatment", "IRS Code Section"],
            "rows": [
                ["Section 179 Expensing", "Immediate expensing up to inflation limits", "IRC Section 179"],
                ["Startup Costs", "First $5,000 expensed, balance over 15 years", "IRC Section 195"],
                ["Business Meals", "Generally 50% deductible if business is discussed", "IRC Section 274"],
                ["Entertainment", "100% non-deductible", "IRC Section 274"]
            ]
        },
        "faqs": [
            {
                "q": "What is the difference between an 'ordinary' and 'necessary' expense?",
                "a": "An ordinary expense is common and accepted in the taxpayer's trade or business. A necessary expense is one that is helpful and appropriate for that trade or business, though it does not have to be indispensable."
            },
            {
                "q": "Are business fines or penalties deductible?",
                "a": "No. Fines or penalties paid to a government entity for the violation of any law are strictly non-deductible under federal tax regulations."
            }
        ],
        "citations": [
            {"name": "Official IRS Publication 535 Page", "url": "https://www.irs.gov/forms-pubs/about-publication-535"}
        ],
        "content": "<p>Publication 535 is critical for EA Exam Part 2 (Businesses). Candidates will face multiple scenario questions where they must decide whether an expense should be capitalized or immediately written off. Pay close attention to rules surrounding automobile expenses, business travel, interest expense limitations, and insurance premiums.</p>",
        "related_topics": [
            {"name": "EA Exam Part 2 Guide", "url": "/en/ea/part/2/"},
            {"name": "Form 1065 Partnership Return Guide", "url": "/en/ea/forms/form-1065-partnership-tax-return/"}
        ]
    },
    "circular-230-rules-governing-practice": {
        "title": "IRS Circular 230: Rules Governing IRS Practice for EA Exam Part 3",
        "meta_description": "Complete breakdown of Treasury Department Circular 230 for EA Exam Part 3. Learn ethical standards, practitioner sanctions, and representation rules.",
        "type": "IRS Publication / Regulation",
        "code": "Circular 230",
        "quick_answer": "Treasury Department Circular 230 contains the regulations governing the practice of attorneys, CPAs, Enrolled Agents, enrolled actuaries, and appraisers before the Internal Revenue Service.",
        "definition": "Circular 230 sets forth the duties and restrictions relating to practice before the IRS, the rules of conduct, and sanctions for violations of these regulations.",
        "key_facts": [
            "Filing of Documents: A practitioner must not delay the prompt disposition of any matter before the IRS.",
            "Conflict of Interest: A practitioner cannot represent a client before the IRS if it involves a conflict of interest, unless written consent is obtained.",
            "Due Diligence: Required as to accuracy in preparing tax returns and documents filed with the IRS.",
            "Sanctions: Disbarment, suspension, censure, or monetary penalties can be imposed for willful violations."
        ],
        "bullet_summary": [
            "Ethical Authority: Circular 230 is the sole regulatory standard for professional practice before the IRS.",
            "Information Request: Practitioners must promptly submit records requested by an officer of the IRS unless privileged.",
            "Knowledge of Error: If a practitioner knows a client has made an error, they must advise the client promptly of the error and its consequences.",
            "Fee Restrictions: Contingent fees are generally prohibited, except for examinations, audits, or judicial proceedings."
        ],
        "stats": {
            "Part 3 Exam Weight": "33% of Exam",
            "Regulatory Code": "31 CFR Part 10",
            "Key Sections": "Subpart B (Duties), Subpart C (Sanctions)",
            "Ethics Credits Required": "2 Hours annually for renewal"
        },
        "table": {
            "headers": ["Circular 230 Section", "Topic", "Key Requirement"],
            "rows": [
                ["Section 10.20", "Information to be Furnished", "Must submit records requested by IRS unless privileged"],
                ["Section 10.21", "Knowledge of Client Error", "Must advise client of error and legal consequences"],
                ["Section 10.22", "Diligence as to Accuracy", "Must exercise due diligence in preparing returns"],
                ["Section 10.27", "Fees", "Contingent fees prohibited for tax preparation"]
            ]
        },
        "faqs": [
            {
                "q": "What happens if an Enrolled Agent violates Circular 230 regulations?",
                "a": "Violations can result in disciplinary action by the IRS Office of Professional Responsibility (OPR), including censure, suspension from practice before the IRS, disbarment, or monetary penalties."
            },
            {
                "q": "What are the rules regarding contingent fees under Circular 230?",
                "a": "A practitioner cannot charge a contingent fee for preparing an original tax return. Contingent fees are allowed only in connection with an IRS examination, an amended return, or judicial proceedings."
            }
        ],
        "citations": [
            {"name": "IRS Circular 230 (PDF)", "url": "https://www.irs.gov/pub/irs-pdf/pcir230.pdf"}
        ],
        "content": "<p>Circular 230 is the single most important document for EA Exam Part 3 (Representation, Practices & Procedures). Nearly one-third of the exam is dedicated to verifying that Enrolled Agents understand their ethical obligations, boundaries of practice, and the disciplinary processes administered by the Office of Professional Responsibility (OPR).</p>",
        "related_topics": [
            {"name": "EA Exam Part 3 Guide", "url": "/en/ea/part/3/"},
            {"name": "Form 2848 Power of Attorney Guide", "url": "/en/ea/forms/form-2848-power-of-attorney/"}
        ]
    }
}

FORMS_DATA = {
    "form-1040-individual-tax-return": {
        "title": "IRS Form 1040: Individual Income Tax Return Guide for EA Exam",
        "meta_description": "Comprehensive guide to IRS Form 1040 for the Enrolled Agent exam. Learn the structure of gross income, AGI, deductions, and tax calculations.",
        "type": "IRS Form",
        "code": "Form 1040",
        "quick_answer": "IRS Form 1040 is the standard federal income tax form used by individual taxpayers to report their annual gross income, claim deductions and credits, and calculate their tax liability or refund.",
        "definition": "Form 1040 consists of multiple schedules (Schedule 1 for additional income/adjustments, Schedule 2 for additional taxes, Schedule 3 for additional credits) that roll up to determine the final tax results for individuals.",
        "key_facts": [
            "Filing Date: Normally April 15th of the following calendar year (unless extended to October 15th via Form 4868).",
            "Filing Statuses: Single, Married Filing Jointly, Married Filing Separately, Head of Household, Qualifying Surviving Spouse.",
            "Adjusted Gross Income (AGI): The line item that governs eligibility thresholds for deductions, credits, and phaseouts.",
            "Schedules A-F: Detail itemized deductions, interest/dividends, business profit/loss, capital transactions, supplemental income, and farming."
        ],
        "bullet_summary": [
            "Core Form: The main interface for individual taxpayers to settle tax accounts with the IRS.",
            "Schedule 1: Essential for reporting self-employment income, unemployment compensation, and educator adjustments.",
            "Page 2 Calculations: Calculates tax liability, self-employment tax, child tax credits, and withholding payments.",
            "EA Exam Focus: Candidates must know which schedules carry specific lines (e.g., Schedule C net income transfers to Schedule 1)."
        ],
        "stats": {
            "Pages": "2 Pages (plus Schedules)",
            "SEE Part Tested": "Part 1 (Individuals)",
            "Filing Extension": "6 Months (via Form 4868)",
            "Statute of Limitations": "Generally 3 years from filing date"
        },
        "table": {
            "headers": ["Form 1040 Section", "Description", "Key Associated Schedule"],
            "rows": [
                ["Lines 1-8", "Gross Income (Wages, Interest, Dividends)", "Form 1040 / Schedule 1"],
                ["Line 11", "Adjusted Gross Income (AGI)", "Form 1040 / Schedule 1"],
                ["Line 12", "Standard or Itemized Deduction", "Schedule A"],
                ["Line 15", "Taxable Income", "Form 1040"],
                ["Lines 25-33", "Payments (Withholding, Estimated Tax, Credits)", "Schedule 3"]
            ]
        },
        "faqs": [
            {
                "q": "What is the function of Schedule 1 on Form 1040?",
                "a": "Schedule 1 is used to report additional income (such as business income, capital gains, rental income, unemployment) and adjustments to income (like student loan interest, self-employed health insurance)."
            },
            {
                "q": "Does Form 4868 extend the time to pay taxes due?",
                "a": "No. Form 4868 grants a 6-month extension of time to file the tax return, but all taxes due must be paid by the original April deadline to avoid interest and failure-to-pay penalties."
            }
        ],
        "citations": [
            {"name": "IRS Form 1040 Page", "url": "https://www.irs.gov/forms-pubs/about-form-1040"}
        ],
        "content": "<p>Form 1040 is the backbone of Part 1. Candidates must know the exact flow of the form: Gross Income -> Deductions to arrive at AGI -> Standard or Itemized Deductions -> Qualified Business Income Deduction (QBID) -> Taxable Income -> Gross Tax -> Nonrefundable Credits -> Other Taxes -> Payments and Refundable Credits -> Refund or Amount Owed.</p>",
        "related_topics": [
            {"name": "IRS Publication 17 Guide", "url": "/en/ea/publications/pub-17-individual-tax-guide/"},
            {"name": "EA Part 1 Study Guide", "url": "/en/ea/part/1/"}
        ]
    },
    "form-2848-power-of-attorney": {
        "title": "IRS Form 2848: Power of Attorney & Representation Guide",
        "meta_description": "Master IRS Form 2848 (Power of Attorney) for the EA Exam Part 3. Learn how to obtain authorization to represent taxpayers before the IRS.",
        "type": "IRS Form",
        "code": "Form 2848",
        "quick_answer": "IRS Form 2848 is used to authorize an eligible individual (such as an Enrolled Agent, Attorney, or CPA) to represent a taxpayer before the IRS and receive confidential tax transcripts and communications.",
        "definition": "The Power of Attorney and Declaration of Representative form establishes the legal authority of a representative to advocate on behalf of a taxpayer, sign agreements, and receive notices for specified tax matters and tax periods.",
        "key_facts": [
            "Eligible Representatives: Enrolled Agents, CPAs, Attorneys, Enrolled Actuaries, and Registered Tax Return Preparers (limited).",
            "Joint Returns: A separate Form 2848 is required for each spouse if a joint tax return is under examination.",
            "CAF Number: Centralized Authorization File number assigned to representatives by the IRS to track authorizations.",
            "Acts Authorized: Receiving transcripts, negotiating settlements, signing consents to extend assessment periods."
        ],
        "bullet_summary": [
            "Taxpayer Rights: Taxpayers have the right to be represented by a qualified professional before the IRS.",
            "Form 2848 vs 8821: Form 2848 allows representation and advocacy; Form 8821 (Tax Information Authorization) only allows disclosure of information.",
            "Signing Authority: A representative cannot sign a tax return unless explicitly authorized on Form 2848 under specific conditions.",
            "Centralized Registry: The CAF unit processes and records Form 2848 submissions to identify authorized practitioners."
        ],
        "stats": {
            "SEE Part Tested": "Part 3 (Representation)",
            "Processing Registry": "CAF (Centralized Authorization File)",
            "Spouse Filing": "Separate forms required",
            "Key Difference": "Representation (2848) vs Info Only (8821)"
        },
        "table": {
            "headers": ["IRS Form", "Representation Rights", "CAF Registry Input", "Receive Notices"],
            "rows": [
                ["Form 2848", "Yes - Full advocacy", "Yes", "Yes (if designated)"],
                ["Form 8821", "No - Information disclosure only", "Yes", "Yes"],
                ["Form 8453", "No - Signature authorization only", "No", "No"]
            ]
        },
        "faqs": [
            {
                "q": "What acts can a representative NOT perform under Form 2848?",
                "a": "A representative cannot endorse or negotiate any check, receive refund checks (unless specifically authorized in Part I), or delegate authority to another practitioner unless explicitly specified."
            },
            {
                "q": "Can an Enrolled Agent sign a tax return for a client?",
                "a": "Only if specifically authorized on Form 2848 and permitted under local tax regulations (e.g., if the taxpayer is absent from the US or suffers from a continuous disease)."
            }
        ],
        "citations": [
            {"name": "IRS Form 2848 Portal", "url": "https://www.irs.gov/forms-pubs/about-form-2848"}
        ],
        "content": "<p>Form 2848 is heavily tested in EA Exam Part 3. You must know how to fill out Part I (Taxpayer Information, Representative Designation, Tax Matters, and Authorized Acts) and Part II (Declaration of Representative - where EAs sign and select designation letter 'C'). Candidates should be clear on the exact timeline for CAF entry and how a Power of Attorney is revoked or withdrawn.</p>",
        "related_topics": [
            {"name": "Circular 230 Regulations", "url": "/en/ea/publications/circular-230-rules-governing-practice/"},
            {"name": "EA Part 3 Guide", "url": "/en/ea/part/3/"}
        ]
    }
}

GLOSSARY_DATA = {
    "ptin-preparer-tax-identification-number": {
        "title": "What is a PTIN? Preparer Tax Identification Number Explained",
        "meta_description": "What is an IRS PTIN? Learn who needs a Preparer Tax Identification Number, how to apply, and its significance for Enrolled Agent exam candidates.",
        "type": "Glossary Term",
        "code": "PTIN",
        "quick_answer": "A PTIN (Preparer Tax Identification Number) is a 9-digit identification number issued by the IRS. It is legally required for anyone who prepares federal tax returns for compensation.",
        "definition": "The IRS uses the PTIN to identify preparers and track tax returns. Under Internal Revenue Code Section 6109, preparing a return for compensation without a valid PTIN can result in monetary penalties.",
        "key_facts": [
            "Format: Starts with the letter 'P' followed by 8 numbers.",
            "Cost: The application is free of cost.",
            "Expiration: PTINs expire on December 31 of each year and must be renewed annually.",
            "Sponsor Requirement: Candidates must have a PTIN to register for the EA Exam."
        ],
        "bullet_summary": [
            "Mandatory Registration: Any paid tax preparer must put their PTIN on tax returns.",
            "SEE Exam Booking: Prometric requires a valid PTIN to register for any of the 3 parts of the EA exam.",
            "Instant Approval: Online applications on the IRS tax professional portal take only 15 minutes.",
            "Public Directory: Valid PTIN holders with professional credentials are listed in the IRS public registry."
        ],
        "stats": {
            "Digits": "9 (starts with 'P')",
            "Annual Renewal Cost": "$0",
            "Application Time": "Instant (online)",
            "Required for SEE": "Yes"
        },
        "table": {
            "headers": ["Registry Type", "Required for Paid Prep", "Allows IRS representation", "Renewal Cycle"],
            "rows": [
                ["PTIN", "Yes - All preparers", "No (unless credentialed)", "Annual (Oct-Dec)"],
                ["CAF Number", "No - Only representatives", "Yes", "Lifetime (unless revoked)"],
                ["EFIN", "Yes - Electronic filing providers", "No", "Continuous"]
            ]
        },
        "faqs": [
            {
                "q": "Can I take the EA exam without a PTIN?",
                "a": "No. When scheduling your Special Enrollment Examination (SEE) via Prometric, you are required to input your IRS-issued PTIN."
            },
            {
                "q": "How do I apply for an IRS PTIN?",
                "a": "You can apply online by creating an account on the IRS Tax Professional PTIN System (irs.gov/ptin) and submitting your personal and business details."
            }
        ],
        "citations": [
            {"name": "IRS PTIN System", "url": "https://www.irs.gov/ptin"}
        ],
        "content": "<p>The PTIN is the foundational ID for every tax professional. For international candidates, getting a PTIN does not require a Social Security Number; you can submit an application along with a notarized passport copy. Once the PTIN is active, you are ready to book your EA exam slots.</p>",
        "related_topics": [
            {"name": "About RISE360 Institute", "url": "/en/ea/about/"}
        ]
    }
}

FAQS_DATA = {
    "ea-exam-cost-breakdown": {
        "title": "Enrolled Agent Exam Cost Breakdown: Total Fees and Expenses",
        "meta_description": "Total cost breakdown to become a US Enrolled Agent in 2025. Learn about Prometric fees, prep course costs, PTIN registration, and licensing fees.",
        "type": "FAQ Topic",
        "code": "EA Cost",
        "quick_answer": "The total cost to become an Enrolled Agent ranges from $900 to $1,500, which includes Prometric exam fees ($206 per part), PTIN registration ($0), prep course materials, and the IRS licensing fee ($140).",
        "definition": "Becoming an EA involves mandatory fees paid to Prometric/IRS and variable costs paid to review course providers. Proper budgeting ensures candidates avoid unexpected financial hurdles during their prep.",
        "key_facts": [
            "Prometric Fee: $206 per attempt, per part (Total $618 for all three parts if passed on first attempt).",
            "IRS PTIN Fee: $0 (Free of cost).",
            "IRS Enrollment Application (Form 23): $140 licensing fee.",
            "LMS Prep Courses: Variable (Free at RISE360 Institute, premium courses can cost $500 - $1,000)."
        ],
        "bullet_summary": [
            "Prometric Fees: Paid per registration block. Retakes require paying the full fee again.",
            "Enrollment Application: Submitted on Pay.gov using Form 23 after passing all 3 parts.",
            "Hidden Costs: Travel to Prometric centers, international candidate fees, or passport renewal.",
            "Zero Cost LMS: RISE360 Institute helps candidates save hundreds of dollars by providing premium-quality MCQs for free."
        ],
        "stats": {
            "Total Mandatory Fees": "$758",
            "Prometric Fee per Part": "$206",
            "Form 23 License Fee": "$140",
            "RISE360 Prep Cost": "$0"
        },
        "table": {
            "headers": ["Expense Item", "Recipient", "Required", "Estimated Cost"],
            "rows": [
                ["PTIN Registration", "Internal Revenue Service", "Yes", "$0"],
                ["SEE Exam Fee (Part 1)", "Prometric", "Yes", "$206"],
                ["SEE Exam Fee (Part 2)", "Prometric", "Yes", "$206"],
                ["SEE Exam Fee (Part 3)", "Prometric", "Yes", "$206"],
                ["Enrollment Application (Form 23)", "IRS / Pay.gov", "Yes", "$140"],
                ["Study Prep Materials", "RISE360 Institute", "Optional", "$0"]
            ]
        },
        "faqs": [
            {
                "q": "What happens if I fail an EA exam part? Do I get a refund?",
                "a": "No. Prometric exam fees are non-refundable. If you fail an exam part, you must schedule a retake and pay the $206 fee again."
            },
            {
                "q": "Are there additional fees for international testing centers?",
                "a": "Yes. Prometric may levy an international surcharge depending on the country (e.g., test centers in India or Europe may have currency conversion or local service surcharges)."
            }
        ],
        "citations": [
            {"name": "Prometric IRS SEE Pricing Info", "url": "https://www.prometric.com/see"}
        ],
        "content": "<p>Properly managing the cost of the EA exam is key. By using RISE360 Institute's high-quality free prep bank, students eliminate the largest variable expense (review materials) and only pay the mandatory government fees to Prometric and the IRS.</p>",
        "related_topics": [
            {"name": "About RISE360 Institute", "url": "/en/ea/about/"}
        ]
    }
}

SALARY_DATA = {
    "enrolled-agent-salary-usa": {
        "title": "Enrolled Agent Salary in USA: Career Path and Earning Potential",
        "meta_description": "Explore the average Enrolled Agent salary in the USA. Learn about entry-level wages, senior tax positions, corporate compensation, and career growth.",
        "type": "Salary Guide",
        "code": "EA Salary US",
        "quick_answer": "The average salary for an Enrolled Agent in the United States ranges from $65,000 to $95,000 per year, with senior tax managers and self-employed practitioners earning well over $120,000 annually.",
        "definition": "An Enrolled Agent's compensation is governed by experience, location (metropolitan vs rural), and sector (public accounting, corporate tax departments, or independent practice).",
        "key_facts": [
            "Average Base Salary: $72,500 per year.",
            "Senior Tax Consultant Salary: $90,000 - $115,000.",
            "Starting Salary (Entry-level): $50,000 - $60,000.",
            "Tax Season Bonuses: Many firms offer profit-sharing or performance bonuses ranging from 5% to 15%."
        ],
        "bullet_summary": [
            "Strong Demand: The IRS shortage of tax auditors and complex tax laws have driven starting salaries up.",
            "Credential Premium: EAs earn 15% to 25% more than non-credentialed tax preparers.",
            "Independent Practice: EAs who open their own tax representation practice can bill $150 to $300 per hour.",
            "Alternative Sectors: Wealth management, corporate payroll, and international tax compliance offer premium rates."
        ],
        "stats": {
            "National Average": "$72,500",
            "Top 10% Earners": "$125,000+",
            "Entry-level Average": "$55,000",
            "Hourly Consultation Rate": "$150 - $300"
        },
        "table": {
            "headers": ["Job Title", "Average Salary (USA)", "Preferred Experience"],
            "rows": [
                ["Junior Tax Staff", "$52,000 - $62,000", "0-2 Years"],
                ["Senior Tax Associate", "$70,000 - $85,000", "3-5 Years"],
                ["Tax Manager (EA)", "$90,000 - $115,000", "5-8 Years"],
                ["Director of Taxation", "$130,000+", "8+ Years"]
            ]
        },
        "faqs": [
            {
                "q": "Does an EA earn as much as a CPA?",
                "a": "While CPAs generally have slightly higher starting salaries due to a broader scope of audit services, Enrolled Agents who specialize in tax representation and business planning achieve parity, often earning equal or higher income as specialized tax experts."
            },
            {
                "q": "What states pay the highest salaries for Enrolled Agents?",
                "a": "Metropolitan states with complex business taxes, such as California, New York, Texas, and Illinois, offer the highest base salaries for EAs, often adjusting for cost of living."
            }
        ],
        "citations": [
            {"name": "Bureau of Labor Statistics Tax Examiners Data", "url": "https://www.bls.gov"}
        ],
        "content": "<p>Earning your EA credential unlocks access to highly stable, high-paying corporate roles and independent practice options. The investment in your SEE exam pays off quickly, as first-year EAs immediately qualify for promotion and salary increases at most accounting firms.</p>",
        "related_topics": [
            {"name": "EA vs CPA Guide", "url": "/en/ea/blog/ea-vs-cpa-which-is-right-for-you/"},
            {"name": "California EA Guide", "url": "/en/ea/state/california-enrolled-agent/"}
        ]
    }
}

STATES_DATA = {
    "california-enrolled-agent": {
        "title": "How to Become an Enrolled Agent in California: Salary & Rules",
        "meta_description": "Step-by-step guide to becoming an Enrolled Agent in California. Salary data, Prometric centers, local tax job market, and state filing requirements.",
        "type": "State Guide",
        "code": "California",
        "quick_answer": "To become an Enrolled Agent in California, pass the three-part IRS Special Enrollment Exam (SEE) and register your credentials. California is one of the highest-paying states for Enrolled Agents, averaging $78,000 - $105,000 annually.",
        "definition": "California has unique state tax agencies (Franchise Tax Board, Board of Equalization) that interact with federal rules. EAs are exempt from California's state preparer registration (CRTP) requirements because they are federally licensed.",
        "key_facts": [
            "Federally Licensed: EAs in California represent clients directly before the IRS and Franchise Tax Board (FTB).",
            "Exemption: Exempt from CTEC (California Tax Education Council) registration.",
            "Top Job Hubs: Los Angeles, San Francisco, San Diego, San Jose.",
            "Prometric Center Locations: Over 15 testing centers across California."
        ],
        "bullet_summary": [
            "No State License Required: EAs represent clients in CA based on federal licensing rules.",
            "High Salary Premium: CA tax complexity drives massive demand for representation experts.",
            "CTEC Exemption: EAs avoid the registration fees and continuing education requirements of standard state tax preparers.",
            "Representation Focus: EAs routinely represent CA clients facing Franchise Tax Board audits."
        ],
        "stats": {
            "Average Salary in CA": "$83,000",
            "CTEC Registration Fee": "$0 (Exempt)",
            "Prometric Center count": "15+",
            "State Tax Agency": "Franchise Tax Board (FTB)"
        },
        "table": {
            "headers": ["California Metro Area", "Average Salary", "Demand Indicator"],
            "rows": [
                ["San Francisco / Bay Area", "$95,000 - $120,000", "Very High"],
                ["Los Angeles Metro", "$80,000 - $100,000", "High"],
                ["San Diego", "$78,000 - $95,000", "Medium-High"],
                ["Sacramento", "$75,000 - $90,000", "Medium"]
            ]
        },
        "faqs": [
            {
                "q": "Do California Enrolled Agents need CTEC registration?",
                "a": "No. Under California law, federally licensed Enrolled Agents are exempt from CTEC registration. EAs represent taxpayers directly before state agencies using their federal credential."
            },
            {
                "q": "Where can I take the EA Exam in California?",
                "a": "You can take the exam at any authorized Prometric testing center in California, including locations in Los Angeles, San Jose, San Francisco, San Diego, and Fresno."
            }
        ],
        "citations": [
            {"name": "California Franchise Tax Board", "url": "https://www.ftb.ca.gov"}
        ],
        "content": "<p>California presents a massive market for Enrolled Agents. The combination of high state tax rates, robust corporate activity, and strict Franchise Tax Board compliance audits ensures a continuous stream of clients needing representation services.</p>",
        "related_topics": [
            {"name": "Enrolled Agent Salary Guide", "url": "/en/ea/salary/enrolled-agent-salary-usa/"}
        ]
    }
}

COUNTRIES_DATA = {
    "india-enrolled-agent": {
        "title": "US Enrolled Agent (EA) Course in India: Career, Salary & Exams",
        "meta_description": "Complete guide to the US Enrolled Agent course in India. Learn about salary in MNCs, Prometric test centers in India, and courses for Chartered Accountants.",
        "type": "Country Guide",
        "code": "India",
        "quick_answer": "The US Enrolled Agent course is highly popular in India, offering average salaries of ₹4,00,000 to ₹9,00,000 per year in Big 4 and US-based MNCs. Exams are conducted at Prometric centers in India (Delhi, Mumbai, Bengaluru, Hyderabad).",
        "definition": "An Enrolled Agent in India specializes in US Federal Taxation, handling tax return preparation and representation audits for US citizens, expatriates, and Indian companies with US subsidiaries.",
        "key_facts": [
            "MNC Employment: High recruitment by Big 4 (Deloitte, EY, KPMG, PwC) and corporate tax firms (Ryan, CohnReznick).",
            "Prometric Center Locations in India: Hyderabad, Bengaluru, Chennai, Mumbai, New Delhi, Ahmedabad, Kolkata, Trivandrum.",
            "Syllabus Bridge: Ideal for Indian Chartered Accountants (CAs) and commerce graduates (B.Com/M.Com).",
            "Exams in India: Testing is open from May 1 to February 28, matching the US testing window."
        ],
        "bullet_summary": [
            "Outsourcing Boom: US tax compliance outsourcing to India has increased EA jobs by 40% year-on-year.",
            "CA Integration: Indian CAs can finish the EA course in 3 to 6 months due to overlapping tax logic.",
            "No Travel Needed: Candidates register online and take all 3 exam parts at local Prometric centers in India.",
            "High Earning Potential: Entry-level EAs earn double the salary of standard accounting graduates in India."
        ],
        "stats": {
            "Average Starting Salary": "₹5,00,000",
            "Prometric Centers in India": "8 Locations",
            "Recommended Study Duration": "4-6 Months",
            "Primary Employers": "Big 4 & US Tax MNCs"
        },
        "table": {
            "headers": ["Indian Metro City", "Average EA Salary", "Primary Employers"],
            "rows": [
                ["Bengaluru / Hyderabad", "₹5,50,000 - ₹9,00,000", "Big 4 Offshore, US MNCs"],
                ["Mumbai / Pune", "₹5,00,000 - ₹8,50,000", "Corporate Tax departments"],
                ["Delhi / NCR", "₹4,80,000 - ₹8,00,000", "Consulting Firms, Outsourced Units"],
                ["Ahmedabad", "₹4,00,000 - ₹7,00,000", "BPO & KPO tax firms"]
            ]
        },
        "faqs": [
            {
                "q": "Where are the Prometric exam centers located in India?",
                "a": "Exams are held at Prometric centers in Bengaluru, Hyderabad, Chennai, Mumbai, New Delhi, Kolkata, Ahmedabad, and Trivandrum."
            },
            {
                "q": "Can a student take the EA exam in India without visiting the US?",
                "a": "Yes. The entire registration and testing process is conducted locally in India at authorized Prometric centers. Licensing forms are submitted online to the IRS."
            }
        ],
        "citations": [
            {"name": "Prometric India Portal", "url": "https://www.prometric.com"}
        ],
        "content": "<p>US tax compliance is one of the fastest-growing sectors in the Indian knowledge-process outsourcing (KPO) sector. Obtaining a US Enrolled Agent license is the most direct path for Indian finance professionals to enter global tax consulting.</p>",
        "related_topics": [
            {"name": "Indian CA to EA Bridge Guide", "url": "/en/ea/blog/how-indian-cas-can-become-us-enrolled-agents/"}
        ]
    }
}


def get_programmatic_page(category, slug):
    """Retrieve programmatic page data based on category and slug."""
    data_map = {
        "publications": PUBLICATIONS_DATA,
        "forms": FORMS_DATA,
        "glossary": GLOSSARY_DATA,
        "faqs": FAQS_DATA,
        "salary": SALARY_DATA,
        "state": STATES_DATA,
        "country": COUNTRIES_DATA
    }
    category_data = data_map.get(category)
    if category_data:
        return category_data.get(slug)
    return None


def get_all_programmatic_urls():
    """Returns a list of tuples (category, slug) for sitemap generation."""
    urls = []
    categories = ["publications", "forms", "glossary", "faqs", "salary", "state", "country"]
    data_map = {
        "publications": PUBLICATIONS_DATA,
        "forms": FORMS_DATA,
        "glossary": GLOSSARY_DATA,
        "faqs": FAQS_DATA,
        "salary": SALARY_DATA,
        "state": STATES_DATA,
        "country": COUNTRIES_DATA
    }
    for category in categories:
        for slug in data_map[category].keys():
            urls.append((category, slug))
    return urls
