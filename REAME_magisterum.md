# Magisterium Psalm Reflection Workflow

This guide covers how to check, develop, run, and automate the new Magisterium-based Psalm reflection flow added to this repo.

## What’s included

New/updated files for this workflow:

- `psalm_fetcher.py` — scrapes the Responsorial Psalm (citation, link, body) from USCCB daily readings.
- `magisterium_client.py` — calls the Magisterium Chat Completions API to generate a Catholic reflection.
- `config_magisterium.py` — config for this workflow (separate from Gemini config).
- `main_magisterium.py` — entrypoint to fetch Psalm, generate reflection, and send email.
- `test_magisterium_client.py` — lightweight unit tests with mocked HTTP responses.
- `.github/workflows/daily-psalm-magisterium.yml` — runs daily at 03:00 GMT+7.
- Updated: `email_sender.py` (supports custom subject and section title), `requirements.txt`, `.env.example`.

## Prerequisites

- Python 3.11 (GitHub Actions uses 3.11)
- A Magisterium API key
- Email credentials (Gmail app password, SendGrid API key, or AWS SES creds)
- Optional Catholic database: `database/LCCMN.SQLite3`

## Setup

1. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. Configure environment

Copy `.env.example` to `.env` (or export env vars in your shell/CI):

- Magisterium

  - `MAGISTERIUM_API_KEY` (required)
  - `MAGISTERIUM_MODEL` (optional, defaults to `magisterium-1`)

- Email
  - `EMAIL_PROVIDER` one of `gmail` | `sendgrid` | `ses` (default: `gmail`)
  - `EMAIL_FROM` (required)
  - `EMAIL_TO` (defaults to `EMAIL_FROM` if omitted)
  - `EMAIL_PASSWORD` (required — Gmail app password, SendGrid API key, or not used for SES)
  - SES extras (only if `EMAIL_PROVIDER=ses`): `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

3. Optional: Catholic Vietnamese verses

Place `database/LCCMN.SQLite3` in the `database/` folder. The client will try to use it to enrich the prompt with Vietnamese verses when a Psalm reference is parsed.

Note on schema: the code expects tables similar to the RVV DB (`books`, `verses` with fields like `book_number`, `chapter`, `verse`, `text`). If your LCCMN schema diverges, adjust `BibleDatabase` or provide a thin adapter.

## How it works

- `PsalmFetcher.fetch_daily_psalm(date)` scrapes USCCB and returns:
  - `date`, `url`, `Psalm` (citation + two newlines + body)
  - `psalm_citation`, `psalm_link`, `psalm_body`
- `MagisteriumClient.generate_psalm_reflection(psalm_content)` builds a prompt and calls Magisterium API, returning the reflection text.
- `main_magisterium.py` wires it together and emails the result. The email subject is "Daily Psalm Reflection - <date>" and the section header reads "Responsorial Psalm".

## Run locally

```bash
# Ensure env vars are set (see Setup). Then run:
python main_magisterium.py
```

If the first run fails (e.g., transient network), just run again. The GitHub Action includes a retry.

## Testing

Lightweight tests use `pytest` and mock the HTTP call:

```bash
python -m pytest -q
```

File: `test_magisterium_client.py`

- `test_generate_psalm_reflection_success` — happy path returns content
- `test_generate_psalm_reflection_empty` — handles empty choices safely

## CI: GitHub Actions

Workflow: `.github/workflows/daily-psalm-magisterium.yml`

- Schedule: every day at 20:00 UTC (03:00 GMT+7 next day)
- Secrets required:
  - `MAGISTERIUM_API_KEY`
  - `EMAIL_FROM`, `EMAIL_TO`, `EMAIL_PASSWORD`
  - If SES: `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- Optional repository vars: `EMAIL_PROVIDER` (defaults to `gmail`)

On failure, the workflow opens a GitHub issue with a link to the failed run.

## Developing and extending

- If USCCB changes HTML structure, adjust the selectors in `psalm_fetcher.py` (`_extract_psalm`).
- For different prompt style, edit `_build_prompt` in `magisterium_client.py`.
- To enrich with more languages/sources, extend `_format_psalm_block` to include extra sections.
- To change when emails are sent, edit the cron in the workflow (remember: 03:00 GMT+7 = 20:00 UTC previous day).

## Troubleshooting

- Import errors: verify Python version and that `requirements.txt` is installed.
- Empty reflection: check your `MAGISTERIUM_API_KEY` and network/firewall. The test uses mocks and does not require a real key.
- Email fails:
  - Gmail: use an App Password and ensure 2FA is enabled.
  - SendGrid: ensure `EMAIL_PASSWORD` holds the API key and sender is verified.
  - SES: confirm region, credentials, and that the sender/recipient are verified (if still in sandbox).
- LCCMN not found: the client logs a warning and continues without verse enrichment.

## Keeping the Gemini Gospel app unchanged

This Psalm/Magisterium flow is fully separate. The existing Gospel/Gemini flow (`bible_fetcher.py`, `gemini_client.py`, `main.py`) is left as-is. No changes required to run both in parallel.

# Documentation:

Making Your First API Request
Setting Up Your API Key
Configure your API key as an environment variable. This approach streamlines your API usage by eliminating the need to include your API key in each request. Moreover, it enhances security by minimizing the risk of inadvertently including your API key in your codebase.

In your terminal of choice:

export MAGISTERIUM_API_KEY=<your-api-key-here>
bash

Or, in your project’s .env file:

MAGISTERIUM_API_KEY=<your-api-key-here>
bash

Replace <your-api-key-here> with your actual API key obtained from the API Console.

Making Your First Request
Execute this curl command in the terminal of your choice:

curl -X POST https://www.magisterium.com/api/v1/chat/completions \
 -H "Authorization: Bearer $MAGISTERIUM_API_KEY" \
 -H "Content-Type: application/json" \
 -d '{
"model": "magisterium-1",
"messages": [
{
"role": "user",
"content": "What is the Magisterium?"
}
]
}'
bash

// npm install magisterium
import Magisterium from "magisterium";

const magisterium = new Magisterium({
apiKey: process.env.MAGISTERIUM_API_KEY,
});

export async function getMagisteriumAnswer() {
const results = await magisterium.chat.completions.create({
model: "magisterium-1",
messages: [
{
role: "user",
content: "What is the Magisterium?",
},
]
});

// Handle the response
console.log(results.choices[0].message);
}
typescript

import requests
import os

api_key = os.getenv("MAGISTERIUM_API_KEY")
url = "https://www.magisterium.com/api/v1/chat/completions"
headers = {
"Authorization": f"Bearer {api_key}",
"Content-Type": "application/json",
}
data = {
"model": "magisterium-1",
"messages": [
{
"role": "user",
"content": "What is the Magisterium?",
}
],
"stream": False
}

chat_completion = requests.post(url, headers=headers, json=data)
print(chat_completion.json()["choices"][0]["message"])
