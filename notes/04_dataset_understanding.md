# 04 — Dataset Understanding

## 1. Purpose of this note

Data science begins with understanding the data, not selecting a model. If we misunderstand what a row, label, date, or missing value means, a technically correct pipeline can still produce an invalid conclusion.

This note explains:

- where the complaint data comes from;
- how a complaint reaches the public dataset;
- the important fields and their relationships;
- the historical narrative archive we need for NLP;
- possible prediction targets and leakage fields;
- selection bias, label drift, publication lag, and other limitations;
- the questions that must be answered during the first data audit.

No dataset has been downloaded and no empirical result is claimed in this note. Counts, missingness, class balance, and usable targets must be measured after we select and verify a fixed snapshot.

## 2. What is the CFPB?

The Consumer Financial Protection Bureau, or CFPB, is a United States government agency concerned with consumer financial products and services.

The CFPB receives complaints involving products such as credit cards, mortgages, consumer loans, debt collection, credit reporting, bank accounts, money transfers, and student loans. It forwards eligible complaints to companies for response and publishes selected complaint information.

Official background:

- [Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/)
- [How the complaint process works](https://www.consumerfinance.gov/complaint/process/)
- [How CFPB shares complaint data](https://www.consumerfinance.gov/complaint/data-use/)

## 3. What does one row represent?

Conceptually, one row represents one complaint record published by the CFPB.

It does **not** represent:

- one unique consumer;
- one verified violation;
- one affected account;
- one financial transaction;
- one unit of consumer harm;
- one randomly sampled person from the population.

A consumer may submit more than one complaint. A complaint is the consumer's reported experience and associated administrative metadata, not an independently verified event.

The `Complaint ID` is the record identifier. During the data audit, we must verify that it is present, non-null, and unique within the selected archive.

## 4. How a complaint reaches the public data

The high-level complaint process is:

```text
Consumer submits a complaint
            |
            v
CFPB reviews and routes it
            |
            v
Company receives the complaint
            |
            v
Company responds, or the publication waiting period passes
            |
            v
Eligible complaint information is published
```

The CFPB states that complaints sent to companies for response are generally published after the company responds, confirming a commercial relationship, or after 15 days—whichever comes first. Complaints referred to certain other regulators are not published in the Consumer Complaint Database.

Historically, a narrative was published only if the consumer consented and after the CFPB took steps to remove personal information.

This process creates important consequences:

- a recently received complaint may not appear immediately;
- not every complaint received by CFPB enters the public database;
- not every published complaint historically contained a public narrative;
- narrative-bearing complaints are a self-selected subset;
- company-response fields occur after the complaint is submitted.

## 5. Critical September 2026 source change

Our original project design assumed that complaint narratives could be obtained from the live Consumer Complaint Database API. That assumption is now outdated.

On August 14, 2026, the CFPB announced that it was ceasing discretionary publication of complaint narratives and visualizations. In the September 2026 database release, complaint narratives and visualizations were removed from the live database.

Previously published narratives were moved to the CFPB FOIA Reading Room. The official archive covers complaints received from December 1, 2011 through August 14, 2026.

Official sources:

- [CFPB announcement dated August 14, 2026](https://www.consumerfinance.gov/about-us/newsroom/the-cfpb-to-cease-discretionary-publication-of-complaint-narratives-and-visualizations/)
- [CFPB Consumer Complaint Database Narratives Archive](https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/)
- [Consumer Complaint Database release notes](https://cfpb.github.io/api/ccdb/release-notes.html)

### Consequence for this project

The NLP parts of this project must use a **fixed historical narrative archive**, not rely on new narratives from the live API.

That affects the project in four ways:

1. The dataset becomes a historical research snapshot rather than a continuously updating live narrative feed.
2. Reproducibility improves because an archived file is fixed.
3. Real-time monitoring of newly published public narratives is no longer possible from the live database.
4. Emerging-risk detection becomes a retrospective historical experiment demonstrating the method, not a claim of current market monitoring.

This does not invalidate the project. It changes the honest framing:

> We will build and evaluate a historical complaint-intelligence and emerging-theme detection system using archived public CFPB narratives.

## 6. Planned data source

The authoritative source for narrative modelling will be the official CFPB Consumer Complaint Database Narratives Archive.

The archive is divided into fixed periods, including:

- September 2023 through March 2024;
- April 2024 through July 2024;
- August 2024 through October 2024;
- November 2024 through December 2024;
- later 2025 and 2026 periods;
- older multi-year archives.

We will not download every archive immediately. In the next acquisition milestone, we will inspect file sizes and schemas, then choose the smallest period that provides:

- enough public narratives for training and evaluation;
- multiple financial products and issues;
- sufficient time coverage for a retrospective emerging-theme experiment;
- manageable storage and training requirements on the local machine.

The chosen file must be recorded with:

- archive name;
- official URL;
- covered complaint-received period;
- download date;
- local filename;
- byte size;
- SHA-256 hash;
- row and column counts after loading.

## 7. Dataset hierarchy

The complaint taxonomy is hierarchical:

```text
Product
   |
   +-- Sub-product
   |
   +-- Issue
          |
          +-- Sub-issue
```

Example structure:

```text
Product: Mortgage
Sub-product: Conventional home mortgage
Issue: Trouble during payment process
Sub-issue: Specific dependent option, when available
```

Important points:

- not every product has a sub-product;
- not every issue has a sub-issue;
- possible issue values depend on the product;
- possible sub-issue values depend on the product and issue;
- taxonomy wording and available choices have changed over time;
- records preserve the choices available when the complaint was submitted.

Therefore, `Issue` cannot always be interpreted independently of `Product`. Two records may use issue labels whose meaning depends on their parent product.

## 8. Initial data dictionary

The table below documents the fields relevant to the project. The exact archived schema must be verified after download.

| Source field | Meaning | Project role | Important caution |
|---|---|---|---|
| `Complaint ID` | Unique complaint record identifier | Traceability, deduplication, retrieval reference | Treat as an identifier, not a numeric measurement |
| `Date received` | Date CFPB received the complaint | Time splitting and theme-volume monitoring | Recent periods can be incomplete because publication is delayed |
| `Product` | Financial product selected by the consumer | Candidate classification target and analysis dimension | Taxonomy changed over time; classes may be imbalanced |
| `Sub-product` | More specific product selection | Analysis or later hierarchical target | Missing for products without sub-products |
| `Issue` | Issue selected by the consumer | Candidate target and theme comparison | Meaning depends on product; taxonomy changed over time |
| `Sub-issue` | More specific issue selection | Detailed analysis | Not available for every issue |
| `Consumer complaint narrative` | Consumer's description of what happened | Primary NLP input | Historical, consent-based, de-identified, unverified, and no longer live-published |
| `Company` | Company named in the complaint | Filtering and descriptive analysis | Complaint volume must not be used as a direct quality ranking without exposure data |
| `Company public response` | Optional public-facing company statement | Retrospective analysis only | Optional and provided after complaint arrival |
| `State` | Consumer-reported mailing state | Geographic analysis | Missingness and population differences affect comparisons |
| `ZIP code` | Published full, partial, or blank ZIP information | Probably excluded from modelling | Privacy-related suppression and mixed formats make interpretation difficult |
| `Tags` | Tags such as Older American or Servicemember | Subgroup analysis only with caution | Potentially sensitive and not necessary for text classification |
| `Submitted via` | Channel used to submit the complaint | Descriptive analysis | Channel distribution can affect narrative availability and style |
| `Date sent to company` | Date CFPB sent the complaint to the company | Process timing analysis | Occurs after receipt and can be post-prediction information |
| `Company response to consumer` | Categorised company response | Retrospective outcome analysis | Post-complaint field; leakage for arrival-time classification |
| `Timely response?` | Whether the company response was timely | Retrospective outcome analysis | Not known when complaint first arrives |

## 9. The narrative field

The complaint narrative is the central NLP input. It contains the consumer's description of the experience in their own words.

Historically, narratives were published only when:

- the consumer chose to share the narrative publicly;
- the complaint was eligible for publication;
- the CFPB completed steps intended to remove personal information.

### What the narrative can contain

- descriptions of financial products and transactions;
- account-servicing problems;
- payment, fee, collection, reporting, or communication issues;
- chronology of events;
- emotional language;
- spelling and grammatical variation;
- masked values or redaction markers;
- repeated text, templates, or copied correspondence;
- multiple issues in the same complaint.

### What the narrative does not guarantee

It does not guarantee that:

- every statement is factually verified;
- the complaint describes a legal violation;
- the company agrees with the account;
- the selected product and issue labels are perfectly correct;
- the text describes only one problem;
- the complaint is representative of other consumers.

The model will learn patterns associated with the dataset's labels. It will not determine whether the underlying allegation is true.

## 10. Missing narratives are not ordinary missing values

A missing narrative does not necessarily mean the consumer provided no description. Historically, a public narrative also depended on consent and publication processing.

Therefore, narrative availability is a selection mechanism.

If we train only on records with public narratives, the model learns from:

> complaints that were eligible for publication and whose consumers' narratives were publicly released under the historical process.

It does not automatically generalise to all complaints received by CFPB or all complaints received by a financial institution.

During the data audit, we must distinguish:

- null narrative values;
- empty or whitespace-only values;
- redaction-heavy but usable narratives;
- extremely short narratives;
- repeated or template-like narratives.

## 11. Candidate classification targets

We have not selected the final first target yet. The decision must be based on the downloaded archive.

### Option A — Predict `Product`

Question:

> Which financial product does this complaint concern?

Advantages:

- easier to explain;
- usually fewer classes than issue prediction;
- likely to provide a stable first baseline;
- product words may be clearly present in narratives.

Limitations:

- can be too easy if the product is explicitly named;
- does not provide detailed issue routing;
- broad products can contain very different problems.

### Option B — Predict `Issue`

Question:

> Which known problem category best matches this narrative?

Advantages:

- closer to complaint-routing value;
- more detailed than product prediction;
- produces a more challenging NLP task.

Limitations:

- many more classes;
- severe class imbalance is possible;
- issue meaning can depend on product;
- label changes across time can complicate evaluation.

### Option C — Predict a combined `Product + Issue` label

Advantages:

- preserves the hierarchy and context;
- avoids treating identical issue wording across products as necessarily equivalent.

Limitations:

- greatly increases the number of classes;
- creates more rare labels;
- makes the first model harder to evaluate and explain.

### Option D — Hierarchical classification

Flow:

```text
Narrative -> predict Product -> predict Issue within that Product
```

Advantages:

- matches the taxonomy structure;
- limits issue choices to the predicted product.

Limitations:

- product mistakes propagate to issue prediction;
- requires several models or a more complex architecture;
- unsuitable as the very first baseline.

### Initial working preference

`Product` is the safest first baseline target, but this remains a hypothesis. We will confirm it only after measuring class counts, narrative coverage, taxonomy consistency, and baseline difficulty.

## 12. Features available at prediction time

The prediction scenario is:

> Suggest a category when a complaint narrative first arrives.

For this scenario, the main legitimate input is the complaint narrative. Some contemporaneous metadata might be available, but using it can reduce generalisability or create shortcuts.

### Safe baseline input

- public complaint narrative text.

### Possible later metadata, requiring justification

- submission channel;
- received date or derived calendar information;
- state;
- other information definitely known at arrival time.

### Fields that must not be baseline features

- true `Product` when product is the target;
- true `Issue` when issue is the target;
- `Sub-product` or `Sub-issue` when they reveal the target hierarchy;
- company response fields;
- timely-response outcome;
- information recorded only after routing or response.

## 13. Target leakage

Target leakage occurs when model inputs contain information that would not legitimately be available when making the prediction or that directly reveals the answer.

Examples:

- predicting `Product` while including `Sub-product`;
- predicting `Issue` while including `Sub-issue`;
- using a company-response field produced after the complaint was processed;
- learning text transformations from the complete dataset before splitting;
- allowing near-duplicate narratives to appear in both training and test sets.

Leakage produces evaluation scores that appear impressive but do not represent real use.

## 14. Time and label drift

The dataset spans many years, and the taxonomy has changed. The CFPB release history records changes to products, issues, sub-products, and sub-issues.

Possible drift includes:

- new financial products;
- renamed or reorganised categories;
- changes in complaint-submission forms;
- changes in consumer vocabulary;
- changes in company behaviour;
- changes in publication policy;
- the August–September 2026 removal of live narratives.

If training and testing use different taxonomy periods, a model can encounter labels it never saw during training.

For the first baseline, a narrower fixed historical period may reduce taxonomy inconsistency. Later experiments can deliberately test temporal generalisation.

## 15. Publication lag and incomplete recent periods

Complaint-received dates and public-release dates are not identical. Complaints are not necessarily published immediately, and historical narratives required additional processing.

Consequences:

- the most recent weeks in a snapshot may be undercounted;
- an apparent decline may reflect incomplete publication rather than a real decline;
- retrospective anomaly detection must avoid treating incomplete periods as ordinary observations;
- the archive cutoff must be recorded.

Because narratives stopped being published on August 14, 2026, the final archive period has a policy cutoff and should not be compared naively with complete earlier periods.

## 16. Selection bias and representativeness

The CFPB explicitly states that the database is not a statistical sample of consumer experiences and is not necessarily representative of all consumers' experiences with a product or company.

Sources of selection include:

- awareness of the CFPB complaint process;
- ability and willingness to submit a complaint;
- whether the complaint is routed to a company;
- consumer consent under the historical narrative-publication process;
- product usage and market size;
- geography and population;
- access to submission channels;
- changes in public attention or reporting behaviour.

Therefore, this project must not claim:

- that more complaints prove a company is worse;
- that a low complaint count proves little harm;
- that complaint percentage equals population prevalence;
- that detected themes represent all consumers;
- that a narrative proves wrongdoing.

## 17. Company and geographic comparisons

Raw complaint counts are influenced by exposure.

For companies, relevant missing context can include:

- customer base;
- market share;
- product mix;
- geographic reach;
- transaction volume.

For states, population and product usage differ.

Without appropriate denominators, company or state counts are descriptive only. The dashboard must avoid league-table interpretations that present raw counts as quality or misconduct rankings.

## 18. Duplicate and near-duplicate risk

There are two distinct questions:

### Duplicate IDs

The same `Complaint ID` appearing more than once can indicate duplicated records in the selected input and should be investigated.

### Near-duplicate narratives

Different IDs can contain identical or highly similar text because of:

- repeated submissions;
- template language;
- copied correspondence;
- recurring descriptions;
- data-processing duplication.

Near duplicates across train and test sets can inflate evaluation because the model has effectively seen the same wording before. We will measure exact narrative duplicates before splitting and consider group-aware handling for strong near duplicates.

## 19. Class imbalance

Some product or issue labels may have far more examples than others.

If one class dominates, a model may achieve high accuracy by favouring that class while failing on smaller categories.

During the audit we must calculate:

- number of unique labels;
- count and percentage for each label;
- ratio between largest and smallest classes;
- classes below minimum sample thresholds;
- label distribution over time;
- narrative availability by class.

This is why macro F1 and per-class recall are planned alongside weighted metrics and accuracy.

## 20. Data types that need careful handling

### Complaint ID

Load as a string even if it contains digits. We do not perform arithmetic on identifiers, and string loading avoids unwanted numeric formatting.

### ZIP code

Load as text, not a number. It can contain leading zeroes, partial values, or missing values. It is unlikely to be needed for the first model.

### Dates

Parse dates explicitly and record invalid values. Do not rely on alphabetical string sorting for temporal splits.

### Yes/no fields

Inspect their actual values before converting them to Boolean values. Missing and unexpected categories must not be silently converted.

### Categorical text

Preserve original labels before creating controlled mappings. Silent label rewriting can destroy traceability.

## 21. Raw, interim, and processed data

### Raw archive

The downloaded official file, preserved without manual edits.

### Interim data

Parsed or filtered records used during audit and transformation, such as records with valid dates and public narratives.

### Processed modelling data

A reproducibly created table containing only the fields and rows approved for a particular experiment.

The raw archive must remain outside Git. Code, configuration, metadata, hashes, validation reports, and small non-sensitive summaries can be versioned.

## 22. Questions for the first data audit

The acquisition and EDA milestones must answer:

### Source and structure

1. Which archive file was selected?
2. What time period does it cover?
3. What is its SHA-256 hash?
4. What does one loaded row represent?
5. Which columns are present, missing, or renamed?

### Quality

6. Are complaint IDs unique?
7. How many dates fail to parse?
8. How many narratives are null, empty, very short, or redaction-heavy?
9. How many exact duplicate narratives exist?
10. Are there malformed rows or inconsistent field types?

### Labels

11. How many product, issue, and combined labels exist?
12. Which labels are rare?
13. How do label counts change over time?
14. Are there labels present only near the beginning or end of the period?
15. Does every issue map consistently to a product?

### Modelling feasibility

16. Is `Product` too easy because product names appear explicitly?
17. Is `Issue` too sparse or unstable for the first baseline?
18. Is there enough data for train, validation, and time-based test periods?
19. Can duplicates cross split boundaries?
20. Which fields are legitimate at complaint-arrival time?

### Emerging-risk feasibility

21. Is the selected period long enough to build a historical baseline?
22. Are complete weekly periods available?
23. Does publication volume change because of source or policy effects?
24. Are discovered themes large and stable enough for weekly monitoring?

## 23. Dataset acceptance criteria

We should proceed to modelling only if:

- the archive comes from an official CFPB source;
- its identity, date range, size, and hash are recorded;
- the schema is documented and validated;
- complaint IDs and dates are usable;
- enough narratives remain after transparent filtering;
- the proposed target has multiple sufficiently represented classes;
- leakage fields are excluded;
- the time range supports the intended validation strategy;
- important selection and interpretation limitations are documented.

If these conditions fail, we will change the archive period or narrow the problem before training a model.

## 24. Initial dataset decision log

| Decision | Current decision | Reason | Verification status |
|---|---|---|---|
| Data authority | CFPB official sources only | Strongest provenance and traceability | Confirmed |
| Narrative source | Official FOIA narrative archive | Live database removed narratives in September 2026 | Confirmed |
| Dataset type | Fixed historical snapshot | Reproducible and compatible with NLP | Confirmed |
| Exact archive file | Not selected yet | File size and schema must be inspected first | Pending |
| First target | `Product` is the working preference | Simpler baseline with fewer expected classes | Pending data audit |
| First input | Complaint narrative only | Avoid shortcut features and leakage | Planned |
| Validation | Time-aware evaluation preferred | Better reflects later complaint language | Pending data coverage |
| Latest periods | Avoid treating incomplete/cutoff periods as normal | Publication lag and August 2026 policy cutoff | Confirmed principle |

## 25. Interview-ready explanation

### “Which dataset are you using?”

> I am using a fixed historical export from the CFPB's official Consumer Complaint Database Narratives Archive. The CFPB stopped publishing narratives in the live database in August 2026 and removed them in its September release, so I use the official FOIA archive rather than assuming the live API still contains narrative text.

### “What does one row represent?”

> One row represents one published complaint record identified by a Complaint ID. It does not necessarily represent one unique consumer, a verified violation, or a random sample of the market.

### “Why are complaint narratives missing or selected?”

> Historically, public narrative availability depended on complaint eligibility, consumer consent, and CFPB de-identification processing. Therefore, narrative-bearing complaints are a selected subset and cannot automatically represent all complaints.

### “What will you predict?”

> Product is my working first target because it is easier to establish as a reproducible baseline. I will confirm that decision only after measuring class balance, taxonomy stability, and how much the narrative directly reveals the product. Issue prediction is more detailed but more imbalanced and dependent on product context.

### “What is target leakage in your project?”

> Leakage would include using sub-product to predict product, sub-issue to predict issue, post-response fields for arrival-time classification, learning TF-IDF from test data, or allowing duplicate narratives across train and test sets.

### “Can complaint volume rank companies?”

> Not responsibly by itself. Raw counts depend on company size, customer base, product mix, reporting behaviour, and other exposure factors. I treat counts as descriptive signals within the dataset, not direct measures of company quality or population-wide harm.

### “Does a complaint prove wrongdoing?”

> No. A complaint narrative presents the consumer's account and is not automatically verified. The system organises historical text and flags patterns for human investigation; it does not determine legal truth.

### “Why is emerging-risk detection retrospective?”

> New narratives are no longer published in the live database. The project therefore replays a fixed historical archive in chronological order to test whether a method could identify unusual theme growth using only information available up to each historical point.

## 26. Completion checkpoint

Before starting acquisition, I should be able to explain:

1. what one complaint row represents;
2. how a complaint reaches the public dataset;
3. why historical narrative availability is selected;
4. what changed in August and September 2026;
5. why we now need the official FOIA archive;
6. how Product, Issue, Sub-product, and Sub-issue relate;
7. why target selection is still pending;
8. which fields would cause leakage;
9. why recent or cutoff periods can be incomplete;
10. why complaint counts are not population prevalence or company rankings.

The key lesson is:

> **The model can only be as defensible as our understanding of what the archived complaint records represent, how they were selected, and which conclusions they cannot support.**

