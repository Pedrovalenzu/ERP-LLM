# Conversational Warehouse Management ERP (LLM Function Calling)

An experimental conversational Enterprise Resource Planning (ERP) prototype designed for automated warehouse inventory control and stock tracking using Natural Language Interfaces (NLI) and Large Language Model (LLM) Function Calling[cite: 2].

Developed for the **Enterprise Information Systems (Sistemas de Información Empresarial)** course at the **University of Málaga (UMA)**[cite: 2].

---

## 📌 Overview

Traditional ERP interfaces require administrative personnel to manually fill out forms, scan barcodes, and query databases through rigid user interfaces[cite: 2]. This project explores the feasibility, performance, and reliability of replacing standard UI workflows with a **purely conversational interface driven by LLM tool usage**[cite: 2].

The system translates natural language queries into executable backend functions (CRUD operations) to manage stock entries (purchases), exits (sales/waste), and real-time inventory queries[cite: 2].

---

## 🚀 Key Features

* **Conversational Inventory Management:** Natural language handling of stock additions, removals, and balance consultations[cite: 2].
* **Function Calling / Tool Integration:** Dynamic mapping of user requests to backend Python database functions and parameter extraction[cite: 2].
* **Real-time Data Visualization:** Automatic generation of dashboard analytics and inventory graphs derived from conversation states[cite: 2].
* **Multi-Model Support:** Architecture tested against both cloud-based APIs and locally hosted open-weights models[cite: 2].

---

## 🧪 Model Comparison & Evaluation

As part of the research, we benchmarked multiple LLMs acting as the orchestration agent[cite: 2]:

| Model | Deployment | Strengths | Limitations Observed |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | Cloud API | High function-calling reliability, fast response times, consistent JSON structure generation[cite: 2]. | Occasional case-sensitivity issues on database entity lookup[cite: 2]. |
| **LLaMA 3.1** | Local Execution | Privacy-preserving, local data sovereignty. | High inference latency, difficulties adhering to function schemas without strict prompt constraints[cite: 2]. |

### Identified Challenges & Trade-offs
1. **Tool Ambiguity:** Smaller or local models frequently struggled to match exact function declarations unless constrained with strict system prompts[cite: 2].
2. **Entity Recognition & Normalization:** Inherent difficulty across models in normalizing user-supplied parameters (e.g., casing inconsistencies when matching existing stock items)[cite: 2].
3. **Data Integrity vs. Usability:** While conversational ERP reduces training overhead, delegating transactional database mutations entirely to LLM interpretation introduces critical risk of state inconsistencies compared to deterministic UI forms[cite: 2].

---

## 🛠️ Tech Stack

* **Language:** Python
* **LLMs & APIs:** Google Gemini API (Cloud)[cite: 2], Meta LLaMA 3.1 (Local)[cite: 2]
* **Tool Calling Framework:** Official Gemini Function Calling / JSON schema definitions[cite: 2]
* **Database & Logic:** Custom backend CRUD functions & stock state management[cite: 2]
* **Visualization:** Python data plotting libraries[cite: 2]

---
