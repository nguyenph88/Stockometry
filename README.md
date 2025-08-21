# Stock Analysis Bot - Milestone 1: Data Collector & Warehouse

This project is the first milestone in building a news-driven stock analysis bot. Its purpose is to reliably collect and store financial news and market data in a PostgreSQL database.

## Features

- **Automated Data Collection**: Fetches data from NewsAPI and Yahoo Finance using a scheduler.
- **Robust Database Setup**: Automatically creates the database and required tables on first run.
- **Configuration Driven**: All API keys, database credentials, and settings are managed via external `.env` and `settings.yml` files.
- **Modern Structure**: Follows best practices for project layout, separating concerns for configuration, data collection, and database management.
- **Idempotent Inserts**: Safely handles duplicate data by ignoring entries that already exist in the database.

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL server running locally or accessible.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd stock_analysis_bot
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the environment:**
    -   Create a `.env` file. You can copy the structure from the example below.
    -   Fill in your `NEWS_API_KEY` and your PostgreSQL connection details.
    -   Review `settings.yml` to adjust tickers or news queries if desired.

## How to Run

1.  **Initialize the Database (Optional - the scheduler does this automatically):**
    You can run the database script directly to create the database and tables manually if needed.
    ```bash
    python src/database.py
    ```

2.  **Run the Scheduler:**
    This is the main entry point for the application. It will initialize the database if needed, run the collection jobs immediately, and then continue running them on schedule.
    ```bash
    python src/scheduler.py
    ```

    The scheduler will run in the foreground. You can stop it with `Ctrl+C`.
