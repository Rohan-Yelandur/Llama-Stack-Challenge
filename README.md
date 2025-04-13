# 📁 File Flow  
_A project built for the **2025 Llama Stack Challenge Hackathon** hosted by 8VC._

🔗 [Devpost Project Page](https://devpost.com/software/fileflow?ref_content=my-projects-tab&ref_feature=my_projects)

---

## 🚀 The Future of File Organization

Enterprise data gets messy fast. Engineers shouldn't have to waste hours organizing files or digging through stale spreadsheets. **File Flow** is an AI-powered agent that intelligently analyzes file **content** and **metadata** to:

- 🔍 **Filter**
- 📂 **Sort**
- 🗑️ **Remove** redundant or unnecessary files

Designed with **data privacy** in mind, File Flow can be run **locally**, ensuring:

- Full control over **costs**
- Lower **latency**
- Enhanced **customization** in relation to model type and fine-tuning.

Currently, the agent supports **local directories** and **Google Drive**, with future plans to support more data management systems.

---

## 🛠️ Tech Stack

- **Llama** — Large Language Model powering the agent  
- **Langchain** — Framework for chaining LLM operations  
- **OAuth** — Secure Google account access  
- **Streamlit** — Frontend interface for interaction  
- **Google Drive API** — Seamless integration with cloud files

---

## 🧪 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Rohan-Yelandur/Llama-Stack-Challenge.git
cd Llama-Stack-Challenge
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Ollama with your choice of local model
Visit https://ollama.com.
Download and install Ollama for your OS.
Start the Ollama service:
```bash
ollama run llama3.2:3b
```
