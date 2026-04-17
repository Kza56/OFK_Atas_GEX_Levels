# Installation Guide — OFK GEX Levels (NQ & ES)

**No programming knowledge required.** Follow each step in order and you'll be up and running in about 15 minutes.

---

## What you will install

| Tool | Purpose | Free? |
|---|---|---|
| Python 3 | Runs the data scripts | ✅ Free |
| 3 Python libraries | Fetch data + generate PDF | ✅ Free |
| Claude Code | AI morning briefing | Requires Claude Pro or Max |
| ATAS indicator | Displays levels on chart | Requires ATAS subscription |

---

## Step 1 — Install Python

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **Download Python** button
3. Run the installer
4. ⚠️ **Important**: check the box **"Add Python to PATH"** at the bottom before clicking Install

![Python installer — check Add to PATH](docs/install_python.png)

To verify it worked, open a terminal (**Win + R → type `cmd` → Enter**) and type:
```
py --version
```
You should see something like `Python 3.14.2`.

---

## Step 2 — Create the working folder

Open a terminal (**Win + R → `cmd` → Enter**) and paste these commands one by one:

```powershell
mkdir C:\gex_agent
mkdir C:\gex_agent\data
mkdir C:\gex_agent\skills
```

---

## Step 3 — Copy the Python scripts

1. Download the repo as a ZIP from GitHub (**Code → Download ZIP**)
2. Extract it anywhere on your PC
3. Open the extracted folder → go into the `python\` subfolder
4. Copy **all `.py` files** into `C:\gex_agent\`
5. Copy **both `.md` files** from `python\skills\` into `C:\gex_agent\skills\`
6. Copy `CLAUDE.md` (from the root of the repo) into `C:\gex_agent\`

Your folder should look like this:
```
C:\gex_agent\
├── run_morning_NQ.py
├── run_morning_ES.py
├── cme_NQ_browser_fetch.py
├── cme_ES_browser_fetch.py
├── data_fetcher_NQ.py
├── data_fetcher_ES.py
├── claude_agent_NQ.py
├── claude_agent_ES.py
├── generate_pdf_NQ.py
├── generate_pdf_ES.py
├── CLAUDE.md
├── data\              (empty folder)
└── skills\
    ├── gex_analyst_NQ.md
    └── gex_analyst_ES.md
```

---

## Step 4 — Install Python libraries

Open a terminal and paste this single command:

```powershell
py -m pip install requests reportlab playwright && py -m playwright install chromium
```

Wait for it to finish (about 1-2 minutes). You'll see a lot of text scrolling — that's normal.

---

## Step 5 — Install Claude Code

You need a **Claude Pro or Max** subscription at [claude.ai](https://claude.ai).

1. Install Node.js from **https://nodejs.org/** (click the LTS version)
2. Open a terminal and paste:
```powershell
npm install -g @anthropic-ai/claude-code
```
3. Then authenticate:
```powershell
claude
```
4. Follow the login prompt — it will open your browser to log in with your Claude account
5. Once logged in, type `/exit` to close

To verify it works:
```powershell
claude --version
```

---

## Step 6 — Test the pipeline (optional but recommended)

Open a terminal, navigate to your folder, and run a quick test:

```powershell
cd C:\gex_agent
py cme_NQ_browser_fetch.py --test-quotes
```

A Chromium browser will open automatically, fetch the NQ spot price, then close. You should see something like:
```
NQ Spot: 19850.50
```

---

## Step 7 — Install the ATAS indicator DLL

You have two options:

### Option A — Use the pre-compiled DLL (easiest)

1. Download `OFK_Suite.dll` from the releases page
2. Copy it into your ATAS indicators folder — replace `YOUR_USERNAME` with your Windows username:
```
C:\Users\YOUR_USERNAME\AppData\Roaming\ATAS\Indicators\
```
> Example: `C:\Users\john\AppData\Roaming\ATAS\Indicators\`
>
> Not sure of your username? Open a terminal and type `echo %USERNAME%`

3. Restart ATAS — the indicators will appear automatically

### Option B — Compile from source

1. Install [VS Code](https://code.visualstudio.com/) and the **C# Dev Kit** extension
2. Install the [.NET 10 SDK](https://dotnet.microsoft.com/download/dotnet/10.0)
3. Download the `OFK_Suite_VSCode.zip` from the repo and extract it
4. Open the `OFK_Suite` folder in VS Code
5. Press **Ctrl+Shift+B** → select **Build and Deploy to ATAS**

This compiles the DLL and copies it automatically to:
```
C:\Users\YOUR_USERNAME\AppData\Roaming\ATAS\Indicators\
```
> The `tasks.json` uses `%USERPROFILE%` so your username is resolved automatically

---

## Step 8 — Add the indicator to your chart

> If ATAS doesn't show the indicators after restart, check that the DLL is in:
> `C:\Users\YOUR_USERNAME\AppData\Roaming\ATAS\Indicators\`

1. Open ATAS and load your NQ or ES chart
2. Click **Indicators** → search for **OFK NQ GEX Levels** or **OFK ES GEX Levels**
3. Double-click to add it to the chart

---

## Step 9 — Configure the indicator settings

Right-click the indicator → **Settings** → go to group **09. Floating Panel**

| Setting | NQ value | ES value |
|---|---|---|
| JSON Path | `C:\gex_agent\data\full_levels_NQ.json` | `C:\gex_agent\data\full_levels_ES.json` |
| Python executable path | `C:\Windows\py.exe` | `C:\Windows\py.exe` |
| Script path | `C:\gex_agent\run_morning_NQ.py` | `C:\gex_agent\run_morning_ES.py` |
| PDF briefing folder | `C:\gex_agent\data` | `C:\gex_agent\data` |

Click **OK** to save.

---

## Step 10 — First run

1. A floating panel will appear on your chart
2. Click **▶ GEX LEVELS NQ** (or **▶ GEX LEVELS ES**)
3. A Chromium browser opens automatically to fetch CME data — **do not close it**
4. Wait ~60 seconds for the full pipeline to complete
5. Levels will appear on your chart and the status bar will show ✅

---

## Daily workflow

**Each morning before RTH open (recommended: 08:45 ET):**

1. Click **▶ GEX LEVELS NQ** or **▶ GEX LEVELS ES**
2. Wait ~60 seconds
3. Click **📄 Briefing** to open the PDF

That's it. The levels are valid for the full session — GEX and OI data update EOD only.

---

## Troubleshooting

**The browser opens but nothing happens**
→ CME may be slow. Wait up to 2 minutes. If it keeps failing, try again later.

**Status shows "Script not found"**
→ Check the Script path setting — make sure it points to the correct `.py` file.

**"JSON not loaded" in the status bar**
→ The pipeline hasn't run yet. Click ▶ GEX LEVELS to run it.

**Claude briefing fails**
→ Make sure Claude Code is installed and authenticated: open a terminal and type `claude --version`.

**PDF not opening**
→ Check the PDF briefing folder setting — it should be `C:\gex_agent\data`.

---

## Requirements summary

| Requirement | Minimum version |
|---|---|
| Windows | 10 or 11 |
| Python | 3.11+ |
| ATAS | Any paid plan |
| Claude | Pro or Max subscription |
| Node.js | 18+ (for Claude Code) |

---

*For questions or issues, open a GitHub issue or ask in the community.*
