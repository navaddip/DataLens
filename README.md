# 🔍 DataLens – GenAI-Powered Data Quality Scoring for Payments

DataLens is a **GenAI-driven data quality analysis platform** designed for the **payments domain**.  
It automatically evaluates payment datasets across standard data quality dimensions and produces a **universal, explainable Data Quality Score (DQS)** with **role-aware insights and actionable recommendations** — while keeping the base score objective and unchanged.

---

## 🚀 Problem Overview

Payment organizations process massive volumes of transaction data across multiple systems.  
Despite its importance, there is **no universal or objective way** to evaluate data quality across key dimensions such as accuracy, completeness, consistency, timeliness, uniqueness, validity, and integrity.

This results in:
- Unreliable analytics and ML models
- Increased regulatory and compliance risk
- Costly manual investigations into data issues

**DataLens solves this by introducing a standardized, transparent, and explainable Data Quality Score (DQS).**

---

## 🎯 Project Objectives

- Automatically analyze any payment dataset securely
- Compute **dimension-level data quality scores**
- Generate a **universal composite DQS**
- Use GenAI to explain data quality issues in plain language
- Provide **prioritized, actionable recommendations**
- Support **role-aware interpretation** without altering the base DQS
- Ensure privacy, governance, and auditability

---

## 🧠 Key Features

### ✅ Universal Data Quality Scoring
- Evaluates datasets across **7 standard dimensions**:
  - Accuracy
  - Completeness
  - Consistency
  - Timeliness
  - Uniqueness
  - Validity
  - Integrity
- Produces a **single, objective DQS (0–100)** per dataset

### 🤖 GenAI-Powered Insights
- Converts technical metadata into **plain-language explanations**
- Highlights **business and regulatory impact**
- Example:
  > “Missing KYC address fields may impact AML compliance and audit readiness.”

### 👥 Role-Aware Interpretation (Non-Intrusive)
- Supports multiple roles:
  - Data Engineer
  - Data Scientist
  - Compliance Officer
  - Fraud Analyst
  - Finance / Settlement
  - Leadership
  - Others
- Role selection **does not change the base DQS**
- Only affects:
  - Explanations
  - Risk emphasis
  - Recommendations

### 🛠 Actionable Recommendations
- Prioritized fixes (High / Medium / Low)
- Estimated DQS improvement for each fix
- Clear guidance on **what to fix next**

### 🔐 Privacy & Governance
- No raw transaction data stored
- Only metadata and scoring outputs are retained
- Audit-friendly and compliance-ready design

---

## 🖥️ Application Flow

1. **Dataset Upload**  
   Upload payment datasets securely (CSV, Parquet, Table, API)

2. **Automatic Quality Analysis**  
   Dataset is evaluated across all relevant data quality dimensions

3. **Universal DQS Generation**  
   A single, objective DQS is computed

4. **Role Selection**  
   Users select how the dataset is being used

5. **GenAI Insights & Recommendations**  
   Role-aware explanations and prioritized improvement actions

---

## 📊 Data Quality Score (DQS)

- Weights are domain-aware and configurable
- Base DQS remains immutable across all roles

---

## 🧩 User Interface Highlights

- Modern, professional fintech dashboard
- Clear visualization of:
  - Overall DQS
  - Dimension-level scores
  - Contribution breakdown
- Role-based insights and recommendation views
- Designed for both **technical and non-technical users**

---

## 🏗️ Tech Stack (Planned / Prototype)

- **Frontend:** Figma (UI/UX), React (planned)
- **Backend:** Python
- **GenAI:** LLM-based explanation and recommendation engine
- **Data Quality Engine:** Rule-based checks
- **Deployment:** Hackathon prototype

---

## 📁 Repository Structure (Proposed)


---

## 🏆 Hackathon Alignment

This project directly addresses **Problem Statement 3**:
> *GenAI Agent for Universal, Dimension-Based Data Quality Scoring in the Payments Domain*

It demonstrates:
- Automation
- Explainability
- Governance
- Domain awareness
- Practical business impact

---

## 📌 Future Enhancements

- DQS trend monitoring over time
- Confidence scoring for DQS reliability
- Dataset comparison across pipelines
- Policy-driven thresholds and alerts
- Exportable audit-ready reports

---

## 👤 Team

- **Project Name:** DataLens
- **Domain:** Payments / FinTech
- **Type:** Hackathon Prototype

---

## 📄 License

This project is developed as part of a hackathon and is intended for educational and demonstration purposes.

---

> **DataLens turns data quality from guesswork into a measurable, explainable trust signal.**


The DQS is calculated as a weighted aggregation of dimension scores:

