# 00 — Project Overview

## 1. Project name

**Financial Complaint Intelligence and Emerging Risk Detection**

The name describes two connected goals:

- **Complaint intelligence:** turning unstructured complaint text into useful information such as predicted categories, related historical cases, and complaint themes.
- **Emerging risk detection:** identifying themes whose complaint volume is increasing unusually quickly and may require investigation.

## 2. Project in one sentence

This project will use natural language processing, machine learning, semantic search, clustering, and time-based anomaly detection to organise financial complaints and help analysts discover growing customer-problem themes earlier.

## 3. The problem in simple language

Customers describe financial problems in their own words. One customer may write “my EMI was charged twice,” while another may write “the bank deducted the instalment two times.” The wording differs, but both complaints may describe the same underlying problem.

When thousands of such narratives arrive, a financial institution must:

1. read and understand each complaint;
2. assign it to the correct product and issue category;
3. send it to the appropriate team;
4. find out whether similar complaints occurred previously;
5. notice whether a particular problem is suddenly becoming more common.

Doing all of this manually is slow and can be inconsistent. Traditional keyword search is also limited because people can describe the same problem using very different words.

## 4. What am I building?

I am building a decision-support system for complaint analysts, risk teams, and product teams. It will eventually contain five main capabilities.

### 4.1 Complaint classification

The system will accept a public complaint narrative and predict its likely financial product or issue category.

```text
Input:
“My instalment was deducted twice and the extra payment was not returned.”

Planned output:
Product: Consumer loan
Issue: Incorrect payment processing
Confidence: 84%
```

This can help with complaint routing, but a human reviewer will remain responsible for important operational decisions.

### 4.2 Similar-complaint retrieval

The system will search historical complaint narratives by meaning rather than relying only on exact keywords. It should recognise that “charged twice,” “duplicate EMI,” and “two instalment deductions” may refer to related problems.

The retrieved complaints can give an analyst historical context and supporting examples.

### 4.3 Complaint-theme discovery

The system will group semantically similar complaints into narrower themes. Existing official labels can be broad, so clustering may reveal more specific patterns inside them.

For example, a broad payment-related category might contain different themes such as duplicate deductions, delayed refunds, payment-posting failures, and incorrect late fees. These are illustrative examples, not findings from the dataset yet.

### 4.4 Emerging-risk detection

The project will count complaints within each theme over time and compare recent activity with historical behaviour.

```text
Previous weekly complaint counts: 8, 11, 9, 13
Current weekly complaint count:   57

Planned signal: unusual increase requiring investigation
```

The system will not claim that an unusual increase proves fraud, misconduct, or a system failure. It will create an alert that directs a human analyst toward a pattern worth investigating.

### 4.5 Dashboard and grounded summaries

SQL will prepare analysis-ready tables, and Power BI will present complaint trends, model results, and emerging-theme alerts.

A later retrieval-augmented generation layer may answer analytical questions using retrieved complaints and calculated results. Its summaries must cite their supporting records and must not replace the underlying analysis.

## 5. Why am I building it?

The project addresses a realistic financial-services problem while providing a meaningful way to learn several areas of data science together:

- working with a real public dataset;
- cleaning and analysing structured and unstructured data;
- building an interpretable text-classification baseline;
- evaluating an imbalanced multiclass problem correctly;
- representing text using sparse features and dense embeddings;
- retrieving and clustering semantically related documents;
- analysing change over time;
- detecting unusual patterns;
- communicating results through SQL and dashboards;
- documenting limitations and responsible-use boundaries.

These components belong to one coherent problem. They are not independent technologies added only to increase the number of resume keywords.

## 6. Who could use it?

### Complaint operations team

This team could use predicted categories and similar cases to route complaints more consistently and investigate them faster.

### Risk and compliance analysts

These analysts could use emerging-theme alerts as early signals that a customer problem deserves closer investigation.

### Product and service teams

These teams could examine recurring complaint themes to understand customer pain points and prioritise operational improvements.

### Data science and model-risk teams

These teams could study model errors, rare-category performance, changing language, confidence calibration, and data drift.

## 7. How will it be useful?

The intended benefits are:

- faster initial organisation of unstructured complaint narratives;
- more consistent category suggestions;
- easier discovery of semantically similar historical complaints;
- earlier visibility into rapidly growing complaint themes;
- evidence-backed investigation through representative source records;
- structured reporting of complaint and model trends;
- transparent evaluation and documented limitations.

These are intended benefits. They must not be presented as measured business impact until the system is implemented and evaluated in an appropriate setting.

## 8. Planned input and output

### Input

The main input will be public records from the Consumer Financial Protection Bureau Consumer Complaint Database. Relevant fields may include:

- complaint narrative;
- product;
- issue and sub-issue;
- date received;
- company;
- state;
- submission channel;
- company response and timely-response status.

The exact schema will be verified when a reproducible dataset snapshot is downloaded.

### Output

Depending on the project stage, the system may produce:

- predicted product or issue labels;
- prediction confidence scores;
- similar historical complaints;
- discovered complaint themes;
- weekly theme-volume tables;
- emerging-theme alerts;
- evaluation reports and error analysis;
- Power BI-ready analytical tables;
- cited summaries of retrieved evidence.

## 9. High-level project flow

```text
CFPB complaint data
        |
        v
Data validation and exploratory analysis
        |
        v
Text preparation
        |
        +-----------------------------+
        |                             |
        v                             v
Complaint classification       Sentence embeddings
        |                             |
        v                       +-----+------+
Predicted category             |            |
and evaluation                 v            v
                         Similar search   Clustering
                                             |
                                             v
                                    Weekly theme counts
                                             |
                                             v
                                    Anomaly detection
                                             |
                                             v
                                    Emerging-risk alerts
                                             |
                                   +---------+---------+
                                   |                   |
                                   v                   v
                             SQL tables         Power BI dashboard
                                                       |
                                                       v
                                            Grounded RAG summaries
```

## 10. What the project will not do

Defining boundaries is important because the word “risk” can otherwise be misunderstood.

This project will not:

- decide whether a person should receive a loan;
- calculate a consumer's creditworthiness;
- set loan pricing or credit limits;
- automatically accuse a company of misconduct;
- prove that an alert represents fraud or an operational failure;
- replace complaint investigators or risk analysts;
- measure the prevalence of financial problems across the full population;
- generate summaries without traceable supporting evidence.

“Risk” in this project means a potentially important complaint pattern that deserves human investigation.

## 11. Why the dataset requires caution

The CFPB complaint database is useful because it contains real complaint metadata and publicly shared narratives. However, it is not a representative sample of every consumer or every financial problem.

The observed complaint volume can be affected by:

- whether consumers know about the complaint channel;
- whether they choose to submit a complaint;
- whether they consent to narrative publication;
- differences in product usage;
- changes in reporting behaviour;
- changes in official categories over time.

Therefore, the project can analyse patterns within submitted CFPB complaints, but it cannot claim that those patterns show the true rate of problems across the entire market.

## 12. Current status

Version-one implementation is complete through:

- verified CFPB archive acquisition, extraction, schema inspection, and EDA;
- chronological, exact-duplicate-isolated classification splits;
- TF-IDF and Logistic Regression training, class-level evaluation, and calibration analysis;
- TF-IDF cosine-similarity retrieval with held-out proxy evaluation;
- 30-topic MiniBatch K-Means clustering and full-dataset assignment;
- prior-only weekly topic monitoring with persistence-based alerts;
- a validated SQLite analytics layer, SQL views, and eight Power BI exports;
- a five-page local Power BI report with privacy and visual QA;
- 51 passing automated tests and a clean Ruff check.

Future extensions, not current claims:

- dense neural embeddings and human-labelled semantic-retrieval evaluation;
- a production API, database, authentication, and scheduled refresh;
- Power BI service publication;
- an evidence-grounded RAG assistant;
- production deployment and operational monitoring.

The verified metrics and dashboard may be discussed with their documented evaluation scope and
limitations. No production impact or deployed-service claim should be made.

## 13. Interview-ready explanation

### 30-second version

> I built a financial complaint intelligence prototype using public CFPB data. It classifies complaint narratives, retrieves lexically similar historical cases, groups complaints into exploratory themes, and monitors weekly topic share for persistent unusual increases. SQL and a five-page Power BI report expose the evidence for human review. It does not make lending decisions or treat an alert as proof of wrongdoing.

### If asked, “Why did you choose this project?”

> I wanted to solve a realistic financial-services problem that required more than training a generic classifier. Complaint narratives combine unstructured text, imbalanced labels, semantic search, unsupervised theme discovery, and temporal anomaly detection. This lets me learn the complete data-science workflow while keeping every component connected to a clear business use case.

### If asked, “What is the most important distinction in the project?”

> Classification assigns a known category to a complaint, while clustering discovers groups without relying entirely on existing labels. Emerging-risk detection then monitors how those groups change over time. These are separate tasks and must be evaluated separately.

## 14. Questions I must be able to answer later

The following questions will be answered with evidence as the project progresses:

1. What exactly does one row in the dataset represent?
2. Which complaints have public narratives, and what selection bias does that create?
3. Should the first target be `Product`, `Issue`, or a controlled combination?
4. How imbalanced are the target classes?
5. Which fields would cause target or temporal leakage?
6. Why is TF-IDF with Logistic Regression a suitable baseline?
7. Which metric best reflects performance across rare categories?
8. How will semantic-retrieval quality be evaluated?
9. How will the quality and stability of complaint clusters be assessed?
10. How will an unusual increase be distinguished from normal variation?
11. How will false alerts be controlled?
12. How will the system be monitored when complaint language changes?

## 15. Key takeaway

The project is not simply a complaint classifier. It is planned as an end-to-end complaint-intelligence workflow:

> **Understand the complaint, find related cases, discover the underlying theme, monitor how that theme changes, and present evidence for human investigation.**

