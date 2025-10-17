# LLM Code Deployment API

This FastAPI-based service automatically builds, deploys, and updates task-specific applications for the **LLM Code Deployment project**.

## 🧩 Features

- Accepts JSON POST requests at `/api/task`
- Verifies a shared secret (`STUDENT_SECRET`)
- Generates minimal web apps using LLM-assisted templates
- Creates public GitHub repos with MIT LICENSE and README.md
- Deploys GitHub Pages via Actions
- Sends evaluation metadata back to the provided `evaluation_url`
- Supports multiple rounds (Round 1 & Round 2)

## ⚙️ Setup Instructions

### 1️⃣ Prerequisites
- Python 3.10+
- Git
- A GitHub Personal Access Token (PAT) with `repo`, `workflow`, and `pages` scopes