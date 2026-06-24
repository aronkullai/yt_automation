# Finance YouTube Automation

Generate paired YouTube Shorts and long-form scripts for a stickman finance channel using the Claude Messages API.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Set `ANTHROPIC_API_KEY` in `.env` or in your shell environment.

## Generate One Script Pair

```powershell
python -m yt_automation.cli generate `
  --pillar 'Compound Interest Stories' `
  --angle 'Investing $100 per month starting at age 18 versus later'
```

The generator writes full JSON responses into `outputs/scripts/` and tracks used topic fingerprints in `outputs/topic_cache.json`.

To inspect the exact prompt without calling Claude:

```powershell
python -m yt_automation.cli generate `
  --pillar 'Compound Interest Stories' `
  --angle 'Investing $100 per month starting at age 18 versus later' `
  --dry-run
```

## Generate From A Topic File

Create a JSON file like `topics.example.json`, then run:

```powershell
python -m yt_automation.cli batch --topics topics.example.json
```

## Output Contract

Claude must return only valid JSON with:

- `pillar`
- `core_idea`
- `short.title`
- `short.script`
- `long_form.title`
- `long_form.script`
- `key_numbers`
- `compliance_flags`

If the first Claude response is not valid JSON, the client retries once with a strict JSON-only correction message.

## Human Review

Always review `compliance_flags` and `key_numbers` before publishing. Generated content is illustrative and should not be treated as individualized financial advice.
