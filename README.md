# Resume Tailor

Paste in a job posting, get a tailored resume and cover letter as PDFs. Powered by Claude.

---

## Requirements

- Python 3.11 or higher
- An [Anthropic API key](https://console.anthropic.com/)

---

## Setup

**1. Install dependencies**

```bash
python3 -m pip install -r requirements.txt
```

**2. Set your API key**

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

> You can add this line to your `~/.zshrc` or `~/.bashrc` so you only have to do it once.

---

## Usage

**Option A — Paste the job posting interactively**

```bash
python3 resume_tailor.py JohnnyTrueman_Resume.pdf
```

The script will prompt you to paste the job posting text. When you're done, type `---` on a new line and hit Enter.

**Option B — Pass the job posting as a text file**

```bash
python3 resume_tailor.py JohnnyTrueman_Resume.pdf stripe_job.txt
```

---

## Output

Your files will be saved to an `outputs/` folder in the same directory as your resume PDF:

```
outputs/
  20260308_Stripe_Senior_Backend_Engineer_Resume.pdf
  20260308_Stripe_Senior_Backend_Engineer_CoverLetter.pdf
```

---

Happy job hunting ~
