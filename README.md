# Telegram Book Library Bot

A Persian digital library Telegram bot built with Python.  
This bot allows users to search, explore, and receive book recommendations from an Excel-based book dataset through Telegram.

## About the Project

This project is a Telegram bot designed for searching and browsing a Persian book library dataset.

Users can search books by title, author, translator, and category. The bot also supports top-rated book listings, random book recommendations, pagination, and Persian-friendly text search.

The project was developed as a practical Python project focused on working with datasets, search logic, Telegram bot development, and user interaction design.

## Features

- Search books by title
- Search books by author
- Search books by translator
- Browse books by category using Telegram buttons
- Show full book details using book codes
- Display top-rated books
- Random book recommendation
- Pagination for long results
- Persian-friendly text normalization and search
- Environment variable management using `.env`

## Technologies Used

- Python
- python-telegram-bot
- Pandas
- OpenPyXL
- python-dotenv
- Excel Dataset

## Project Structure

```text
Digital_library/
│
├── bot.py
├── phase1_dataset.py
├── phase2_search_engine.py
├── book_dataset_6000.xlsx
├── requirements.txt
├── README.md
├── .gitignore
└── .env.example
```

## How to Run

Clone the repository:

```bash
git clone https://github.com/mahansafa/Digital_library.git
cd Digital_library
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
```

Run the bot:

```bash
python bot.py
```

## Environment Variables

This project uses a `.env` file to keep the Telegram bot token private.

Example:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
```

The real `.env` file should not be uploaded to GitHub.

## Dataset

The bot uses an Excel dataset named:

```text
book_dataset_6000.xlsx
```

The dataset includes book information such as:

- Book title
- Author
- Category
- Translator
- Publisher
- Original publication year
- Number of pages
- Rating

## What I Learned

Through this project, I practiced:

- Building Telegram bots with Python
- Working with Excel datasets using Pandas
- Designing search functions
- Normalizing Persian text for better search results
- Managing user interactions with buttons
- Handling pagination in Telegram messages
- Using environment variables for sensitive data
- Structuring a Python project for GitHub

## Project Status

Completed.  
The bot currently runs locally using polling and is not deployed on a server yet.

## Team

**Project Manager & Lead Developer:** Mohammad Mahan Safaiyan  
**Collaborator:** Pardis Jadid Eslami

## Author

Developed by Mohammad Mahan Safaiyan and Pardis Jadid Eslami.
