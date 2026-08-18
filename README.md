# Eleva

**Eleva** is an AI-powered **Decision Agent** specialized in marketing for e-commerce and retail businesses.

It analyzes company data, identifies problems and opportunities, reasons over the available information and marketing knowledge, and generates structured, actionable recommendations.

Eleva combines deterministic data analysis with Large Language Models (LLMs) to provide reliable and explainable marketing decisions.

---

## What Eleva Does

Eleva transforms raw business data into actionable marketing recommendations through a structured decision process:

**Data → Analysis → Detection → Knowledge Retrieval → Reasoning → Planning → Decision → Recommendation**

The system can:

- Import customer, order, and campaign data from CSV files.
- Automatically map CSV columns to the required data structure.
- Clean and validate imported data.
- Calculate marketing KPIs and customer segments.
- Perform RFM (Recency, Frequency, Monetary) customer segmentation.
- Detect marketing problems and opportunities using business rules.
- Retrieve relevant marketing knowledge from playbooks using RAG.
- Analyze detected issues and formulate hypotheses using an LLM.
- Generate and prioritize marketing strategies.
- Produce structured and explainable recommendations.
- Generate customer-level recommendations using RFM segments and business rules.

---

## Decision Engine

The **Decision Engine** is the core of Eleva.

It processes each analysis through eight sequential steps:

1. **Understand** — identifies the company context and objectives.
2. **Observe** — analyzes business data and calculates KPIs and customer segments.
3. **Detect** — identifies problems and opportunities using predefined business rules.
4. **Retrieve** — retrieves relevant marketing playbooks using RAG.
5. **Reason** — analyzes the detected issues and available knowledge using an LLM.
6. **Plan** — generates possible marketing strategies.
7. **Decide** — evaluates and prioritizes the proposed strategies.
8. **Recommend** — produces structured and actionable recommendations.

This separation allows Eleva to combine deterministic calculations with LLM-based reasoning while keeping recommendations explainable.

---

## Data

Eleva works with three main types of business data:

- **Customers** — customer profiles and behavioral information.
- **Orders** — transaction and purchasing history.
- **Campaigns** — historical marketing campaign performance.

Data is isolated by company, ensuring that each company's information remains separated from other companies' data.

---

## RAG and Marketing Knowledge

Eleva uses **Retrieval-Augmented Generation (RAG)** to provide the reasoning process with relevant marketing knowledge.

Marketing playbooks are stored as structured YAML documents and indexed using **Chroma**.

When a problem is detected, Eleva retrieves the most relevant knowledge before generating strategies. This allows recommendations to be based on structured marketing guidance rather than relying only on the LLM's general knowledge.

---

## LLM Integration

Large Language Models are used for tasks that require flexible language understanding and reasoning, including:

- CSV column mapping.
- Analysis of possible causes of detected issues.
- Generation of marketing strategies.
- Formulation of structured recommendations.

Deterministic operations such as KPI calculations, RFM segmentation, validation, and business rules are handled by the application logic.

---

## Technology Stack

- **Python 3.12**
- **FastAPI**
- **Streamlit**
- **Groq / Llama 3.3 70B**
- **LangChain**
- **Chroma**
- **Pydantic**
- **Pandas**
- **python-dotenv**

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/lakhmaisszineb/Eleva.git
cd Eleva
