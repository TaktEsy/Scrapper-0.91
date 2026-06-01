# Scrapper v0.91 – parser with Cloudflare bypass and automatic IP rotation

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 📌 Features
- Parsing pages protected by Cloudflare Turnstile.
- Automatic IP rotation on ban (via router reboot).
- Retry attempts for pages with no data.
- Tkinter GUI (start, pause, stop, log).

## 🚀 Quick Start
### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Download EdgeDriver and place it into `drivers/`
4. Configure `config.py` for your router
5. Run: `python main.py`

## 🧠 How it works
1. The program starts.
2. A request is sent to a specific website (in this case list-org.com).  
   (The necessary search filters are configured via GET parameters in the URL.)
3. The entire page is downloaded. The required parameters are extracted.
4. If the site bans our IP, the application reboots the router, so the ISP assigns us a new IP.
5. The algorithm repeats from step 2.

## 🖼️ Screenshots
<img width="755" height="686" alt="image" src="https://github.com/user-attachments/assets/7e673035-8522-4851-a45d-adaab23a6ca5" />

## 📄 License
MIT
