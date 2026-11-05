# DME Document Generator — Local Edition

A small Flask application for generating DME-branded PDF invoices locally.

## Requirements
- Python 3.10+
- pip

## Setup (Ubuntu / WSL)

```bash
cd dme-document-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

Stop the server with `Ctrl+C` in the terminal.

## Notes
- Generated PDFs are saved in `generated/`.
- The invoice counter is stored in `data/numbering.json`.
- Add the approved DME logo at `static/images/dme_logo.png` to show it in generated PDFs.
- This is an early local prototype. Do not expose the development server to the public internet.
- Keep customer records, generated PDFs, secrets, and local data out of a public GitHub repository.
