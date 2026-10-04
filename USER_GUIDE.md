# Evidence Research — User Guide

A complete guide to installing, configuring, using and deploying the Evidence Research app.

**Contents**
1. [Introduction](#1-introduction) · 2. [What the Agent Does](#2-what-the-agent-does) · 3. [Key Features](#3-key-features) · 4. [Project Structure](#4-project-structure) · 5. [Requirements](#5-requirements) · 6. [Complete Local Setup (Windows)](#6-complete-local-setup-windows) · 7. [Using the App](#7-using-the-app) · 8. [Understanding the Research Process](#8-understanding-the-research-process) · 9. [Understanding the Final Report](#9-understanding-the-final-report) · 10. [Ollama Setup and Usage](#10-ollama-setup-and-usage) · 11. [Cloud API Setup](#11-cloud-api-setup) · 12. [Exporting Reports](#12-exporting-reports) · 13. [Research History](#13-research-history) · 14. [Troubleshooting](#14-troubleshooting) · 15. [Deployment Guide](#15-deployment-guide) · 16. [Example Workflow](#16-example-workflow) · 17. [Important Notes and Limitations](#17-important-notes-and-limitations)

---

## 1. Introduction

**Evidence Research** is a Streamlit web app that researches a topic you type and produces a cited report. Every key finding in the report is shown as **Claim → Evidence → Source → Verification**, so you can see exactly where each statement came from and how well it was checked.

**Purpose:** give you a fast, transparent first pass over the evidence on any question.

**Problem it solves:** ordinary search gives you a pile of links, and chat answers can sound confident without showing proof. This app searches several databases, scores the sources, keeps only claims whose supporting quote can be found in a real source, flags disagreement and uncertainty, and lists every source with a clickable link.

---

## 2. What the Agent Does

You can research **any topic or question you enter**. The three example prompts on the New Research screen are only suggestions: clicking one just fills the text box, and you can replace it or ignore it. Whatever is in the box when you click **Start research** is exactly what gets researched.

The agent works through six stages, in order:

| # | Stage | In plain language |
|---|---|---|
| 1 | **Planning** | Breaks your topic into sub-questions and writes web and academic search queries. |
| 2 | **Searching** | Runs the queries in parallel on DuckDuckGo (web), OpenAlex (scholarly works) and Crossref (publication records). |
| 3 | **Evaluating** | Removes duplicates, scores each source's credibility, and drops sources with no readable text or a score below your threshold. |
| 4 | **Verifying** | Pulls result-bearing sentences from the sources (not definitions or "this paper aims to…" text), then checks each quote against its source and looks for a second source that supports it. |
| 5 | **Conflict checking** | Compares the verified findings and flags genuine disagreements. |
| 6 | **Writing** | Assembles the report: introduction, findings, perspectives, statistics, method notes, conclusion and references. |

---

## 3. Key Features

| Feature | What it gives you |
|---|---|
| Any-topic research | Type any topic or question. |
| Multi-source search | DuckDuckGo + OpenAlex + Crossref, searched in parallel. |
| Live research progress | Stage tracker, current search queries, real counts and an activity log. |
| Source evaluation | A 0–100 credibility score and a source type label for each source. |
| Evidence verification | Each finding's quote must be found in its source text; unmatched claims are removed. |
| Corroboration | Findings supported by a second source are marked **Verified**; otherwise **Partially verified**. |
| Citations | Clickable numbered citations such as **[1]** and a full References list. |
| Evidence Map | A table linking each claim to its sources, verification, confidence and evidence type. |
| Confidence and uncertainty | High / Moderate / Low confidence, correlation-versus-causation warnings and caveats. |
| Different Perspectives | Shown only when a genuine disagreement is detected. |
| Important Statistics | Shown only when a number appears inside a verified evidence quote. |
| Standard / Deep Dive | Two research depths. |
| Research History | Every finished research task is saved separately and can be reopened or deleted. |
| Settings | Light/Dark theme, AI provider and model, research limits, trust options, export preferences. |
| Ollama and Cloud API | One provider setting used by the whole agent. |
| Bring Your Own API Key (BYOK) | For Cloud API, each user enters their own key in Settings. It lives only in that user's session and is never saved to a file. |
| PDF / DOCX export | Download any saved report. |

---

## 4. Project Structure

```text
app.py              The Streamlit app (screens, buttons, report display)
requirements.txt    Python packages to install
.env.example        Template for your .env settings file
.gitignore          Files Git should not upload (.env, .data/, exports)
README.md           Short setup summary
USER_GUIDE.md       This guide
.streamlit/         Streamlit configuration (config.toml)
agents/             The research workflow steps
    planner.py        Planning
    researcher.py     Searching (parallel searches, de-duplication)
    evaluator.py      Source scoring and filtering
    verifier.py       Finding extraction and verification
    conflicts.py      Conflict checking
    reporter.py       Report assembly
    orchestrator.py   Runs the stages in order and saves the result
services/
    llm.py            The single connection to Ollama or a Cloud API
    export.py         PDF and DOCX creation
tools/              The three search sources (web_search.py, openalex.py, crossref.py)
models/             Data definitions (schemas.py)
utils/              Settings, history storage, text helpers, theme (config.py, history.py, text.py, theme.py)
exports/            Generated PDF/DOCX copies are saved here
.data/              Created on first run: settings.json and history/ (one file per research task)
```

You normally only edit `.env`; everything else is changed from the app's Settings screen.

---

## 5. Requirements

| Need | Details |
|---|---|
| **Python** | Python 3.10 or newer recommended. |
| **Packages** | Listed in `requirements.txt`: `streamlit>=1.40`, `requests>=2.31`, `ddgs>=9.0`, `python-docx>=1.1`, `reportlab>=4.0`, `python-dotenv>=1.0`. |
| **Internet** | Required for DuckDuckGo, OpenAlex and Crossref searches (and for Cloud APIs). |
| **An AI model** | Either **Ollama** (local, free) or a **Cloud API** key. One of the two is required. |
| **Ollama** | Installed and running, with at least one model downloaded. Any chat model that Ollama can run works; the app lists whatever you have installed. |
| **Cloud API key** | Only if you choose Cloud API (OpenAI, Anthropic, Google Gemini, OpenRouter, Groq or a custom OpenAI-compatible service). **Each user brings their own key** and enters it in the app (see [section 11](#11-cloud-api-setup)). |
| **Accounts for the search sources** | None. DuckDuckGo, OpenAlex and Crossref need no key. |

---

## 6. Complete Local Setup (Windows)

### Step 1 — Install Python
1. Download Python from <https://www.python.org/downloads/>.
2. Run the installer and **tick "Add python.exe to PATH"** before clicking *Install Now*.
3. Open **PowerShell** and check:
   ```powershell
   python --version
   ```

### Step 2 — Open the project
1. Unzip the project (for example to `C:\evidence-agent`).
2. In File Explorer open the project folder, click the address bar, type `powershell` and press Enter. (Or run `cd C:\evidence-agent` in PowerShell.)
3. Confirm you are in the right place — you should see `app.py`:
   ```powershell
   dir
   ```

### Step 3 — Create and activate `.venv`
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
Your prompt now starts with `(.venv)`.

> **If activation is blocked** ("running scripts is disabled"): run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer *Y*, then activate again. Alternatively, in Command Prompt (cmd) use `.venv\Scripts\activate.bat`.

### Step 4 — Upgrade pip and install packages
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5 — Configure `.env` (optional)
```powershell
copy .env.example .env
notepad .env
```

| Variable | Purpose |
|---|---|
| `OLLAMA_HOST` | Ollama address. Default `http://localhost:11434`. |
| `LLM_API_KEY` | **Optional** default Cloud API key for your own local use. Not required: Cloud API users enter their own key in the app, and a key entered in the app always takes priority. Leave it empty if you want every user to bring their own key. |
| `LLM_BASE_URL` | Only used when the Cloud provider is **Custom (OpenAI-compatible)**. |
| `CONTACT_EMAIL` | Optional email sent to OpenAlex/Crossref for more reliable access. |

Save the file. Never share or upload `.env`. You can skip this step entirely: the defaults work for Ollama, and Cloud API users enter their own key inside the app.

### Step 6 — Set up Ollama (if using Ollama)
1. Install Ollama from <https://ollama.com/download> and start it (it runs in the background after install).
2. Download a model, for example:
   ```powershell
   ollama pull llama3.1
   ```
3. Check that Ollama is running and which models exist:
   ```powershell
   ollama list
   curl.exe http://localhost:11434/api/tags
   ```
See [section 10](#10-ollama-setup-and-usage) for more.

### Step 7 — Configure Cloud API (if using Cloud API)
No file setup is needed. After the app starts, go to **Settings → AI / Model → Cloud API** and enter **your own** API key (Bring Your Own Key). It is kept only in your current session and is not saved to any file, so you may need to enter it again after reloading the page. See [section 11](#11-cloud-api-setup).

> *Optional:* if the app is only for you, you may put `LLM_API_KEY=...` in `.env` as a default. A key typed in the app always takes priority over it.

### Step 8 — Start the app
With `(.venv)` active, in the project folder:
```powershell
streamlit run app.py
```

### Step 9 — Open the app
Streamlit prints a **Local URL**. Open <http://localhost:8501> in your browser if it does not open automatically.

### Step 10 — Choose your model
Go to **Settings → AI / Model**, pick the provider, click **Check connection / refresh models**, and select a model. For Ollama use the default host `http://localhost:11434` (section 10); for Cloud API enter your own key first (section 11). Continue when the page shows **✅ Ready**.

### Stopping and restarting
- **Stop:** click in the PowerShell window and press `Ctrl + C`.
- **Restart later:** open PowerShell in the project folder, activate and run again:
  ```powershell
  .venv\Scripts\Activate.ps1
  streamlit run app.py
  ```
  (You do not need to reinstall packages.)

---

## 7. Using the App

The left sidebar has four pages — **New Research**, **Research History**, **Settings**, **Export** — and shows the active model name at the bottom.

### 7.1 New Research

| Control | What it does |
|---|---|
| **Research topic or question** | Large text box. Type any topic or question. |
| **Example prompts** (three buttons) | Fill the text box with a suggestion. They never change how research works; edit or replace the text freely. |
| **Research depth** | **Standard** (faster) or **Deep Dive** (more searches, sources and findings; slower). |
| **Start research** | Starts the agent. Shows a warning if the box is empty, or an error if the model is not configured. |
| **Model line** | Shows which provider and model will be used. |

If **Start research** shows a red message instead of starting, the model is not ready — open **Settings → AI / Model** and follow the ⚠️ message there.

When research completes, the report appears below. On later visits to New Research, the most recent report is shown under "Latest research".

### 7.2 Live progress panel
Appears immediately after you click **Start research**:

| Item | Meaning |
|---|---|
| **Stage chips** | The six stages with ✅ done, ⏳ running, ○ waiting. Below them: **Current** and **Next** stage. |
| **Now** | What the agent is doing this moment. |
| **Active searches** (🔎 lines) | Queries currently being searched and which collection (Web (DuckDuckGo), Scholarly works (OpenAlex), Publication records (Crossref)). |
| **Searches** | Completed / total searches. |
| **Raw results** | Total results returned by all searches. |
| **Unique sources** | Results left after removing duplicates. |
| **Sources kept** | Sources that passed evaluation and go on to verification. |
| **Claims checked** | Candidate findings extracted from the sources. |
| **Findings** | Findings that survived verification. |
| **Live activity log** | The most recent actions, with timestamps. |

### 7.3 The report
Sections: Introduction, Key Findings, Different Perspectives (only if relevant), Important Statistics (only if relevant), Evidence Map, How We Checked, Conclusion, References, and an **Export this report** button. See [section 9](#9-understanding-the-final-report).

### 7.4 Research History
Lists every completed research task (topic, date, depth, number of findings and references, model). **Open** shows the full report; **Delete** removes it; **← Back to history** returns to the list. See [section 13](#13-research-history).

### 7.5 Settings
Five tabs. Changes are saved automatically.

| Tab | Controls |
|---|---|
| **Appearance** | **Theme:** Light or Dark (near-black). |
| **AI / Model** | **Provider:** Ollama or Cloud API. Ollama: host URL, **Check connection / refresh models**, model. Cloud API: a notice that you bring your own key, **Cloud provider**, base URL (Custom only), **Your API key** (password field) with a status line, **Check connection / refresh models**, model. A line at the bottom shows ✅ Ready or what is missing. See [section 11](#11-cloud-api-setup). |
| **Research** | Default research depth; max sources analysed for Standard (6–14) and Deep Dive (12–30); model call timeout (30–300 s); search timeout (5–60 s). |
| **Trust & verification** | Minimum source credibility score (0–80); Prefer scholarly sources; Drop single-source findings from low-credibility sources; Strict quote matching. |
| **Export** | Default format (PDF/DOCX); include Evidence Map; include evidence quotes; include process log. |

Trust options in plain words:
- **Minimum source credibility score** — sources scoring below it are discarded (default 25).
- **Prefer scholarly sources** — gives academic sources a scoring bonus.
- **Drop single-source findings from low-credibility sources** — removes findings supported by only one source scoring below 50.
- **Strict quote matching** — requires about 90% of the quote to match the source text (instead of about 75%).

### 7.6 Export
Choose a saved research task, a format (PDF/DOCX), what to include (Evidence Map, Evidence quotes, Process log), click **Generate file**, then **Download**. See [section 12](#12-exporting-reports).

---

## 8. Understanding the Research Process

**Source collections**
| Collection | What it is |
|---|---|
| Web (DuckDuckGo) | General web results (news, institutions, organisations, blogs). |
| Scholarly works (OpenAlex) | Academic papers with abstracts. |
| Publication records (Crossref) | Journal and publication records with abstracts. |

**How much is searched**

| | Standard | Deep Dive |
|---|---|---|
| Searches | 8 (3 web, 3 OpenAlex, 2 Crossref) | 13 (5 web, 5 OpenAlex, 3 Crossref) |
| Results per search | up to 6 | up to 8 |
| Default max sources analysed | 10 | 20 |
| Max findings in report | 8 | 14 |

If one search fails or times out, the agent says so in the log and continues. If every search fails, the run stops with an error.

**Source counts.** *Raw results* → *Unique sources* (duplicates removed by DOI/link/title) → *Sources kept* (readable text of at least 60 characters, score at or above your minimum, within the source cap).

**Credibility score and source type.** Each source gets a 0–100 score from its type, domain (e.g. government, university, major publishers, news outlets), citation count, recency and amount of text. The type label is one of: *Scholarly publication*, *Preprint (not peer-reviewed)*, *Institution / major publisher*, *News outlet*, *Encyclopedia (background only)*, *General web*, *Low-trust web*. The score is a guide, not a guarantee.

**Verification.**
1. The agent selects sentences that report actual results (effects, comparisons, associations, statistics, conclusions) and that relate to your question. Aims, definitions and background sentences are skipped.
2. The quote must be found in the source's text. Claims whose quote is not found are **removed** (they never appear in the report; the count appears in *How We Checked*).
3. The agent looks for a second source that supports the claim.

| Status | Meaning |
|---|---|
| **Verified** ✅ | Quote found in its source **and** at least one other source supports the claim. |
| **Partially verified** 🟡 | Quote found in its source, but no second source corroborated it. Treat with caution. |
| **Conflicting** | Not a status label; disagreements appear in **Different Perspectives**. |
| **Unverified** | Quote not found in the source. These claims are removed and counted in *How We Checked*. |

**Confidence.** *High* — verified by multiple sources and credibility of at least 60. *Low* — model certainty low or credibility under 40. *Moderate* — everything else. Confidence is separate from verification: it also reflects source quality.

**Evidence type.** *Causal*, *correlational* or *descriptive*. Correlational findings show a warning that association is not causation; causal findings remind you to check the study design in the source.

**Conflict checking.** A rule-based comparison (no model call) that flags two findings from different sources when they cover the same subject but point in opposite directions (an increase versus a decrease, or an effect versus no effect). It needs at least two findings.

**Where the AI model is used.** Planning (queries), optional rewording of the top few claims into short sentences (if it fails, the original source sentences are kept), and the report's introduction and conclusion (a standard text is used if it fails). Searching, scoring, quote checking, corroboration and conflict checking are done by the app's own code.

---

## 9. Understanding the Final Report

| Section | Meaning |
|---|---|
| **Introduction** | Short framing of the topic. |
| **Key Findings** | Each finding is a card: **Claim** (with citation numbers), **Evidence** (the quote from the source), **Source** (clickable title, source type, credibility), **Verification** (status, confidence, explanation). Warnings for correlation and caveats may follow. |
| **Different Perspectives** | Appears **only** when a genuine disagreement was detected. Shows the findings that point in different directions and why differences may exist. |
| **Important Statistics** | Appears **only** when a number/percentage appears inside a verified evidence quote. |
| **Evidence Map** | Table: # · Claim · Sources · Verification · Confidence · Evidence type. Use it to see at a glance which claims rest on several sources and which on one. |
| **How We Checked** | Real counts: searches completed/failed, raw results and unique sources, sources kept and dropped, claims checked/verified/removed, and whether conflict checking ran. Expand **Queries used and limitations** to see the search queries and the method's limits; expand **Process log** for the timed log. |
| **Conclusion** | Summary of what the evidence supports and where it is uncertain. |
| **References** | Numbered sources with authors, year, venue, clickable title and source type. |

**Reading citations.** A citation like **[2]** is a link to the source; the number matches the References list. A claim with several numbers is supported by several sources. If no findings pass verification, the report says so — try a more specific topic or **Deep Dive**.

> **Tip:** For anything important, open the cited sources and read them. The report is a transparent starting point, not a final authority.

---

## 10. Ollama Setup and Usage

1. **Install and start Ollama** from <https://ollama.com/download>. It runs in the background.
2. **Download a model** (any name from Ollama's library), e.g. `ollama pull llama3.1`.
3. **Check Ollama and its models:**
   ```powershell
   ollama list
   curl.exe http://localhost:11434/api/tags
   ```
4. **In the app:** Settings → AI / Model → Provider **Ollama**.
5. **Host URL:** keep `http://localhost:11434` unless Ollama runs elsewhere (or set `OLLAMA_HOST` in `.env`).
6. Click **Check connection / refresh models**. Success shows "Connected — N model(s) available" and the **Model** dropdown fills with your installed models.
7. **Select a model.** The sidebar and the New Research screen show the active model; Settings shows ✅ Ready.
8. Go to **New Research** and start.

**Common Ollama problems**

| Problem | Fix |
|---|---|
| "Could not reach http://localhost:11434" | Ollama is not running. Start it from the Start menu, then click **Check connection / refresh models**. |
| Model list is empty | No model downloaded. Run `ollama pull <model>` and refresh. |
| "Select a model…" message | Choose a model in Settings → AI / Model. |
| Model call timed out | The model is too slow for your machine. Choose a smaller model, close other heavy programs, or raise the model call timeout in Settings → Research. |
| Wrong host | Correct the Ollama host URL in Settings (and `OLLAMA_HOST` if you set it). |

---

## 11. Cloud API Setup

The Cloud API option uses **Bring Your Own Key (BYOK)**: you use **your own** API key from a cloud provider. The app does not supply a key for you, and the key you enter is used only for **your** session.

### 11.1 Step by step

1. Open **Settings → AI / Model**.
2. Set **Provider** to **Cloud API**. A blue notice appears explaining that you bring your own key and that it is kept only in your browser session.
3. Choose a **Cloud provider**: OpenAI, Anthropic, Google Gemini, OpenRouter, Groq, or **Custom (OpenAI-compatible)**.
   - For every provider except Custom, the base URL is filled in automatically and shown as *Base URL: …* — there is nothing to type.
   - For **Custom**, enter the **Base URL (OpenAI-compatible)** of your service, for example `https://host/v1`.
4. Paste your key into **Your API key** and press **Enter**. The field hides what you type.
5. Check the status line directly under the key box (see 11.2).
6. Click **Check connection / refresh models**. On success you see "Connected — N model(s) available." and the **Model** dropdown fills with your provider's models. If the provider does not return a list, a **Model name** text box appears — type the model name manually.
7. Select a **Model**.
8. Confirm the bottom line shows **✅ Ready**, then go to **New Research**.

### 11.2 Status messages

| Where | Message | Meaning |
|---|---|---|
| Under the key box | **Using your session key.** | Your key is entered and will be used for your research. |
| Under the key box | **No key entered yet.** | You have not entered a key. |
| Under the key box | **No key entered — using the server's default key.** | Appears only if the app's owner configured a default key (`LLM_API_KEY`). Enter your own key to use it instead. |
| Bottom of the tab | **✅ Ready** | A model, a key (yours or the server's default) and a base URL are all set. |
| Bottom of the tab | **⚠️ Select a model in Settings → AI / Model.** | Click **Check connection / refresh models** and choose a model. |
| Bottom of the tab | **⚠️ Add your API key in Settings → AI / Model (or LLM_API_KEY in .env).** | No key is available. Enter your own key in the key box. |
| Bottom of the tab | **⚠️ Set the host / base URL in Settings → AI / Model.** | Only for **Custom**: enter the base URL. |

### 11.3 How your key is handled

- Your key is stored **only in your current Streamlit session** (your browser tab's session). Sessions of different users are separate.
- It is **not** written to the settings file, Research History, reports, exports, logs or any project file.
- It is used only to make your session's model calls to the provider you selected. A key you enter takes priority over any server default.
- When your session ends, you reload the page, or the app restarts, **you may need to enter the key again.**

> **Security:** never publish your API key in GitHub, screenshots, reports or chat messages. Do not paste it into any file in the project. If a key is exposed, revoke it in your provider's dashboard and create a new one.

Your choices of provider and model (not the key) are saved in the app's settings.

### 11.4 Example: OpenRouter

1. Create an account at <https://openrouter.ai> and create **your own** API key there.
2. In the app: **Settings → AI / Model → Provider: Cloud API**.
3. Set **Cloud provider** to **OpenRouter**. The page shows *Base URL: `https://openrouter.ai/api/v1`* automatically.
4. Paste your OpenRouter key into **Your API key** and press **Enter**; the status line shows **Using your session key.**
5. Click **Check connection / refresh models**, then select a model.
6. When **✅ Ready** appears, start your research from **New Research**.

> **Do not** enter `http://localhost:11434` for a Cloud API. That address is only for Ollama running on the same computer as the app (section 10).

### 11.5 Common problems

| Problem | Fix |
|---|---|
| Key box is empty after reloading the page | Expected: the key is kept only for the session. Enter it again. |
| "Add your API key…" | No key entered. Paste your key in **Your API key** and press Enter. |
| API error 401 / 403 | Wrong key, expired key, or the key belongs to a different provider than the one selected. |
| API error 404 / model not found | Refresh models and choose one from the list, or check the model name you typed. |
| Cannot list models | Check the provider selection, the base URL (Custom only) and your internet access; type the model name manually if needed. |
| Ready never appears | Read the ⚠️ message at the bottom of the tab — it names what is missing (model, key or base URL). |

---

## 12. Exporting Reports

1. Open **Export** (or click **Export this report** under any report).
2. Pick the **Research task**.
3. Choose **PDF** or **DOCX**.
4. Toggle **Evidence Map**, **Evidence quotes**, **Process log**.
5. Click **Generate file**, then **Download**.

A copy is also saved in the project's `exports/` folder as `<task id>.pdf` or `<task id>.docx`.

**Included:** title and details (depth, date, model), Introduction, Key Findings (claim, optional evidence quote, source, verification, caveats), Different Perspectives and Important Statistics (when present), optional Evidence Map, How We Checked, optional Process log, Conclusion, and References. Citations and reference URLs are clickable links.

> **Note:** PDF export uses a standard font; unusual characters may be replaced with `?`.

---

## 13. Research History

- Each finished research run is saved automatically as its own file in `.data/history/` inside the project folder.
- **Open** to view the whole report again, **Delete** to remove it, **Export** from the opened report to download it.
- Runs that fail or are stopped before finishing are not saved.
- Deleting a history item does not delete files already saved in `exports/`.

---

## 14. Troubleshooting

| Problem | What to do |
|---|---|
| `python` is not recognised | Python is missing or not on PATH. Reinstall and tick **Add python.exe to PATH**, then open a new PowerShell. |
| `.venv` will not activate | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use `.venv\Scripts\activate.bat` in cmd. |
| `ModuleNotFoundError` | Activate `.venv` first, then run `pip install -r requirements.txt`. |
| `streamlit` is not recognised | `.venv` is not active, or packages are not installed. Activate and install, or run `python -m streamlit run app.py`. |
| Port already in use | Another app is using 8501. Run `streamlit run app.py --server.port 8502`. |
| Browser cannot open the app | Make sure the terminal is still running Streamlit, and open <http://localhost:8501>. |
| Ollama cannot connect / model not found | See [section 10](#10-ollama-setup-and-usage). |
| Cloud API fails | See [section 11](#11-cloud-api-setup). |
| On a deployed app, Ollama does not connect | Expected: a deployed app cannot reach Ollama on your own computer. Choose **Cloud API** and enter your own key. |
| I have to enter my API key again | Expected: the key is kept only in the current session and is not saved. |
| "All searches failed or returned nothing" | Check your internet connection and try again; search services can briefly rate-limit. |
| "No usable sources with readable text" | Rephrase the topic, or lower the minimum credibility score in Settings → Trust & verification. |
| Report has zero findings | No claim passed verification. Use a more specific question or **Deep Dive**. |
| Research takes too long | Use **Standard**; pick a smaller/faster model; lower the max sources in Settings → Research; check your connection. Searches and individual model calls have time limits and the run continues past a failure. |
| App looks stuck after changing code or settings | Press `Ctrl + C` in the terminal and start it again. |

---

## 15. Deployment Guide

The appropriate platform for this project is **Streamlit Community Cloud** (it runs `app.py` directly from a GitHub repository). It can also run on any server or VM that can run Python and Streamlit.

### 15.1 Local Ollama versus deployed Cloud API

| | Local use | Deployed app |
|---|---|---|
| Model provider | **Ollama** on your own computer | **Cloud API** (for example OpenRouter, OpenAI, Anthropic) |
| Ollama host | `http://localhost:11434` | Not usable (see below) |
| API key | Not needed for Ollama | **Each visitor enters their own key** in Settings → AI / Model → Cloud API |
| Cost | Free (your hardware) | Billed to each visitor's own provider account |

> **Important:** a deployed Streamlit app **cannot access Ollama running on the owner's computer**. On a server, `localhost` means the server itself, not your PC. Visitors of a deployed app should choose **Cloud API**. Use Ollama on a server only if that server runs Ollama (or can reach one) and `OLLAMA_HOST` points to it.

### 15.2 BYOK for visitors

With Bring Your Own Key, **the project owner does not need to share a personal API key with visitors**. Each visitor opens **Settings → AI / Model → Cloud API**, picks a provider (for example **OpenRouter**), enters **their own** key, selects a model and starts research. Their key stays in their own session, is used for their research and is never saved to the server's settings, history or reports. They may need to enter it again after reloading the page or after their session ends.

### 15.3 Streamlit Community Cloud

1. **Prepare the project.** Make sure these exist at the top level: `app.py`, `requirements.txt`, and the folders `agents/`, `services/`, `tools/`, `models/`, `utils/` (and `exports/`).
2. **Create a GitHub repository** and upload the project. `.gitignore` already keeps `.env`, `.data/`, `.venv/` and generated exports out of the repository — **never upload `.env` or any API key**.
3. **Sign in** at <https://share.streamlit.io> with GitHub and click **Create app**.
4. **Settings:** choose your repository and branch, and set **Main file path** to `app.py`. Streamlit installs packages from `requirements.txt` automatically.
5. **Secrets (optional).** With BYOK you do **not** need to add an API key. You may add `CONTACT_EMAIL = "you@example.com"` (more reliable OpenAlex/Crossref access) or `LLM_BASE_URL` for a Custom provider. Secrets use this format:
   ```toml
   CONTACT_EMAIL = "you@example.com"
   ```
   Add `LLM_API_KEY` **only** if you deliberately want a default key that visitors without their own key will use (and you will pay for). Leave it out for strict bring-your-own-key use.
6. Click **Deploy**. When the app starts, tell visitors to open **Settings → AI / Model**, choose **Cloud API**, pick a provider, enter their own key, click **Check connection / refresh models**, and select a model.

### 15.4 Server / VM
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```
Set `OLLAMA_HOST` (only if using Ollama on the server) as an environment variable or in `.env`, and put the app behind a reverse proxy or firewall. `LLM_API_KEY` is optional and only needed if you want a default key.

> **Warnings:**
> - The app has **no login**. Anyone who can open the URL can run research, see saved history and change Settings. History and settings (provider/model choices, not API keys) are stored on the server and shared by everyone using the same running copy.
> - If you set `LLM_API_KEY` on the server, visitors who enter no key will use it and run up **your** costs. Leave it unset for BYOK.
> - History and settings are stored in `.data/` on the server. On hosts with temporary storage, they may be lost when the app restarts or redeploys.

---

## 16. Example Workflow

0. Make sure **Settings → AI / Model** shows **✅ Ready** (Ollama: model selected; Cloud API: your own key entered and a model selected).
1. Open **New Research** and click the example **"What does research say about microplastics and human health?"** — or type any topic of your own. Keep **Standard** selected.
2. Click **Start research**. The progress panel appears immediately.
3. Watch the stages: **Planning** (queries are created), **Searching** (🔎 lines show queries per collection and the **Searches** counter rises), **Evaluating** (**Unique sources** and **Sources kept** fill in), **Verifying** (**Claims checked** and **Findings** fill in), **Conflict checking**, **Writing**. The activity log shows each step with timings.
4. When the report appears, read **Key Findings**. For each, note the status (✅ Verified or 🟡 Partially verified), the confidence, and any correlation warning.
5. Inspect evidence: read the quoted **Evidence**, click the **[n]** citation or the source title to open the original, and check the credibility score and source type.
6. Review the **Evidence Map** to see which claims have several sources, then **How We Checked** to see how many claims were removed, and **Different Perspectives** if it appears.
7. Open **Research History** from the sidebar. Your research is listed; click **Open** to view it again.
8. Click **Export this report** (or open **Export**), choose **PDF** or **DOCX**, click **Generate file**, then **Download**.

---

## 17. Important Notes and Limitations

- **Verification checks the text the search returned** — usually an abstract or snippet — not the full paper. A verified quote means it appears in that text, not that the study is flawless.
- **Credibility scores are heuristics** (source type, domain, citations, recency, amount of text). They are not a substitute for expert review.
- **Findings come from sentences in the sources.** Wording shown as a claim may be the source's original sentence if the model rewording was skipped or failed.
- **Conflict checking is rule-based** and only catches clear opposite directions on overlapping subjects. Subtler disagreements may not be flagged, so read the findings yourself.
- **Correlation is not causation.** Correlational findings are labelled; check study design before drawing causal conclusions.
- **Search coverage is limited** to what DuckDuckGo, OpenAlex and Crossref return at that moment; relevant work can be missed, and search services may occasionally fail or rate-limit (the run continues if only some fail).
- **Standard is faster, Deep Dive is broader but slower.** Speed also depends heavily on your Ollama model and hardware.
- **Reports may contain few or no findings** for narrow or obscure topics.
- **PDF export** uses a standard font, so some special characters may be replaced.
- **Settings and history are local to the running copy** of the app (`.data/`), shared by everyone using it, and there is no user login.
- **Your cloud API key is session-only.** It is not saved to settings, history, reports or any project file, so you may need to enter it again after your session ends or the page is reloaded.
- **A deployed app cannot use your local Ollama.** Deployed use requires a Cloud API and each visitor's own key (unless the owner sets a default `LLM_API_KEY`).
