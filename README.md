# YouTube-Channel-Scraper-Python-
A flexible YouTube scraping tool that automatically finds channels by keywords and extracts detailed metadata: subscribers, contacts, emails, social links, and more. Originally built for freelance tasks to collect auto-content channels, but fully adaptable for searching and analyzing any niche or topic.

A lightweight Python utility for collecting structured data about YouTube channels.
Designed primarily for analysts, researchers, marketers, and freelancers who need fast access to metadata from multiple channels or niches.

Originally created for a freelance task to extract channels for auto-content projects, but fully adaptable for any niche or topic.

🚀 Features

🔍 Search channels by keywords

📌 Extract channel URL, title, description

👥 Normalize and parse subscriber count

✉️ Detect emails and contact information

🌐 Extract social links (Telegram, Instagram, websites, etc.)

📊 (Optional) Get last-30-days view statistics via YouTube Data API

📁 Export results to CSV and Excel (.xlsx)

🧠 Smart HTML parsing fallback when API is not available

🛠 Installation
git clone https://github.com/Ansar667/youtube-channel-scraper.git
cd youtube-channel-scraper
pip install -r requirements.txt

🔑 Setting Up API Key (Optional)

Create .env file:

YOUTUBE_API_KEY=your_api_key_here


If no API key is provided, the scraper still works using HTML-based parsing.

▶️ Usage

Edit search queries inside main.py:

SEARCH_QUERIES = [
    "автоконтент",
    "психология",
    "фитнес",
]


Then run:

python main.py


Results will appear as:

youtube_channels.csv
youtube_channels.xlsx

📂 How It Works

Performs keyword-based YouTube search

Collects unique channel URLs

Fetches /about page of each channel

Extracts:

Title

Description

Subscribers

Emails

External links

(Optional) Uses YouTube API to calculate last-30-days views

Saves everything into spreadsheets

The scraper focuses only on collecting accurate YouTube channel metadata.
It does NOT download videos or bypass platform restrictions.

🧰 Use Case Example (Freelance)

A client needed to gather hundreds of channels in a specific niche (auto-content) including contacts and subscriber statistics.
This tool automated the process and reduced manual work from hours to minutes.

You can reuse it for:

Niche research

Influencer/creator discovery

Competitor analysis

Market segmentation

Collecting leads across YouTube

📄 Requirements
requests
beautifulsoup4
pandas
openpyxl

📘 Project Structure
src/
│
├── main.py              # Main runner
├── youtube_html.py      # HTML parsers
├── youtube_api.py       # API integrations
├── parsers.py           # Smaller parsing utilities
└── utils.py             # Shared helper functions

📥 No Future Development Planned

This utility was created specifically for a freelance project.
It is provided “as is” for anyone who finds it useful.

📜 License

MIT License — free to use, modify, and extend.
