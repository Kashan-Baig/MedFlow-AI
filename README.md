## latest changes by hassan ( UV package manager intiialized )
---

### first run
cd app
uv sync
### to run workflow run 
uv run python -m src.ai.workflows.patient_flow
### to run backend run 
uv run uvicorn main:app --reload


## ⚙️ Setup Instructions

Follow these steps to set up and run the project locally.

---

### 🐍 1. Create Virtual Environment (Python 3.10.3)

Make sure you have **Python 3.10.3** installed.

Create a virtual environment:

```bash
python -m venv venv
```

---

### ▶️ 2. Activate Virtual Environment

#### On Windows (PowerShell):

```bash
venv\Scripts\activate
```

#### On macOS/Linux:

```bash
source venv/bin/activate
```

After activation, you should see `(venv)` in your terminal.

---

### 📦 3. Install Dependencies

Install all required packages using:

```bash
pip install -r requirements.txt
```

---

### 🔐 4. Setup Environment Variables

Create a `.env` file in the root directory of the project and add the following:

```env
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_DOC_PDF_URL=https://docs.google.com/document/d/YOUR_DOC_ID/export?format=pdf
```

> ⚠️ Make sure your Google Doc is set to **"Anyone with the link can view"**

---

### 🚀 5. Run the Project 

```bash
python app.py
```

*(Replace `app.py` with your main file if different)*

---

### ⚠️ Notes

* Always activate the virtual environment before running the project
* Do not commit `.env` file to GitHub (add it to `.gitignore`)
* Use Python **3.10.3** for compatibility
* Ensure all dependencies are installed correctly

---
