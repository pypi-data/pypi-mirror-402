# gensecureAI 🛡️

**AI-powered Python Security Scanner** with GUI-based vulnerability detection and **auto-fix support**.

`gensecureAI` statically scans Python source code to detect common security issues and provides **safe remediation suggestions** with optional **auto-fix**.

---

## 🚀 Features

✅ SQL Injection Detection  
✅ OS Command Injection Detection  
✅ Hardcoded Secret Detection  
✅ Dangerous Function Usage (`eval`, `exec`, `pickle`)  
✅ GUI-Based Review & Auto-Fix  
✅ Safe Code Rewrite Option  
✅ Modular & Importable Library  

---
## 🔥 Advanced Features (v2)

1. AST Diff Guard – Validates AI fixes at AST level to prevent unrelated/hallucinated code changes
2. Vulnerability-Aware Prompting – LLM prompt dynamically adapts based on detected CWE vulnerabilities
3. Fix Correctness Validator – Ensures AI-generated fix compiles and preserves functionality
4. Trust Score Engine – Calculates reliability score for each fix (0–100%)
5. Attack Path Visualization – Maps input → vulnerable code → potential exploit
6. Plugin-Based CWE Rules – Easily add new vulnerability detection rules without touching core
7. Research Metrics Export – Export scan results, risk scores, and AI fixes in JSON/CSV
8. Explainable AI Fix – Human-readable reasoning for applied security fixes
9. CI / Headless Mode – Automated scans and fixes in pipelines without GUI
10. Zero-Hallucination Strict Mode – Rejects any fixes that modify unrelated code or introduce new dependencies
---

## 📦 Installation

```bash
pip install gensecureAI
