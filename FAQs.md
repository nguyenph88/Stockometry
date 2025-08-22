# Stockometry - Frequently Asked Questions

## 📊 Stock Selection Strategy

### Q: How do we determine which stocks to track? Should we track all stocks or focus on specific symbols?

**A:** That's a critical strategic question. You should start by focusing on a curated list of specific, influential stock symbols rather than attempting to track all of them.

Tracking every single stock is impractical and inefficient, especially in the early stages of a project. Here's a breakdown of why the focused approach is better and the reasoning behind the specific stocks chosen.

#### 🎯 **Why Focus on a Small Group of Stocks First?**

- **API & Resource Limits**: Free APIs have strict limits on how many requests you can make per minute or per day. Trying to pull data for thousands of stocks would exhaust your quota almost instantly, making the bot unusable.

- **Data Overload**: Collecting and storing data for every stock would require a massive database and significant processing power. It's better to prove the concept on a manageable dataset first.

- **Analytical Focus**: Your goal is to find a signal in the noise. A smaller, more relevant dataset makes it easier to develop, test, and refine your NLP and prediction models. Once your logic is proven, you can expand its scope.

- **Cost-Effectiveness**: This approach keeps potential costs for data storage and processing very low while you are building and testing the core functionality.

#### 🏆 **The Rationale for Choosing AAPL, MSFT, GOOGL, AMZN, and NVDA**

The stocks included in the `settings.yml` file were not chosen randomly. They are **bellwether stocks** or **market movers**.

These are massive, influential companies whose performance often has a ripple effect across the entire market. Here's why they are a perfect starting point:

- **High News Volume**: These companies are constantly in the news, providing a rich stream of text data for your NLP models to analyze.

- **Sector Indicators**: They represent the core of the technology and consumer discretionary sectors. News that affects them often indicates a broader trend for their entire industry. For example, a new regulation impacting Google's advertising business will likely affect other digital ad companies as well.

- **High Trading Volume & Liquidity**: Their price movements are significant and are followed by the entire investment community. This makes them excellent subjects for testing your model's ability to correlate news events with tangible market reactions.

- **Economic Significance**: These companies are so large that major news about them can sometimes impact the entire S&P 500 or NASDAQ indices. By tracking them, you are essentially keeping a pulse on the health of the broader economy.

**In short**, this initial list acts as a high-signal, manageable starting point to build and validate your bot's core logic before you scale up.

---

## 📈 Historical Trend Analysis

### Q: Is it a good idea for historical trends to span our last 6 days but not 3, 4 days?

**A:** That's an excellent question. It gets to the core of the strategy behind the trend analysis. Using a 6-day window is a deliberate choice to balance responsiveness with reliability.

Here's the thinking behind it:

#### ⚡ **Why Not 3-4 Days?**

A shorter window is highly responsive but can be easily misled by short-term "noise." For example, a single positive news story could create a 2-day positive trend that isn't significant and quickly fades. A shorter window is more likely to give you **false signals**.

#### 🎯 **Why 6 Days?**

This period is long enough to filter out the daily noise. If a sector shows consistently positive sentiment for 5-6 consecutive days (roughly a full trading week), it's a much stronger indication that a real, underlying trend is forming. It's a more **robust and reliable signal**.

#### ⏰ **Why Not Longer (e.g., 30 Days)?**

A much longer window would be too slow. It would become a **lagging indicator**, only confirming a trend long after the opportunity has passed.

#### 🎯 **The Sweet Spot**

Ultimately, **6 days is a strategic sweet spot**. It's designed to be:
- **Long enough** to ensure the trend is real
- **Short enough** to still be a useful, predictive signal

---

## 📈 A patient analyst, not a hyperactive trader

### Q: With the algorithm, some days it does not have any signal in the report. Is it a bug? I thought it's supposed to give some signals (or at least one) daily.

**A:** Yes, that is absolutely correct and is the intended design of the algorithm. It's a feature, not a bug. The bot is designed to act like a patient analyst, not a hyperactive trader. Its primary goal is to identify high-confidence opportunities, and those don't happen every single day.

Here's the thinking behind it:

#### ⚡ **The "Confluence" Requirement**

Think of the bot's logic as needing two key pieces of evidence to align before it raises an alert:

1. A Historical Trend (The "Why"): Is there a consistent, multi-day sentiment for a sector? This establishes the underlying market mood.

2. A Daily Catalyst (The "Now"): Did a specific, high-impact news event happen today that reinforces that trend?

A high-confidence signal is only generated when both of these conditions are met.

#### 🎯 **Why 6 Days?**

This period is long enough to filter out the daily noise. If a sector shows consistently positive sentiment for 5-6 consecutive days (roughly a full trading week), it's a much stronger indication that a real, underlying trend is forming. It's a more **robust and reliable signal**.

#### ⏰ **Scenarios With No Signal**

The bot will correctly remain silent in several common scenarios:

1. Trend Without a Catalyst: The Technology sector might have a positive trend, but if today's news is neutral and boring, there's no immediate reason to act. The bot waits.

2. Catalyst Without a Trend: A big, positive news event might happen for the Energy sector, but if there's no underlying positive trend, the bot sees it as an isolated event, not a high-confidence signal.

3. Conflicting Information: The Technology sector has a positive trend, but a negative high-impact event (like a new regulation) happens today. The bot recognizes this as uncertainty and correctly produces no signal.

This selective approach is what makes the bot's signals valuable. When it does issue a report, it's because multiple, independent conditions have aligned, making the prediction much more reliable than a system that forces an opinion every day.

---

## 🔗 **Related Documentation**

- **[README.md](README.md)** - Project overview and quick start
- **[EXAMPLE.md](EXAMPLE.md)** - Complete output structure and examples
- **[README_RUNE_ONCE.md](README_RUNE_ONCE.md)** - Independent runner documentation
- **[WHAT_THIS_TOOL_DOES.md](WHAT_THIS_TOOL_DOES.md)** - Core concept explanation

