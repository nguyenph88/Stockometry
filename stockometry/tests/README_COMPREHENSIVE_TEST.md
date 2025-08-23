# Comprehensive End-to-End Test for Stockometry

## 🎯 Purpose

This comprehensive test validates the **entire Stockometry workflow** from data collection to API endpoints. It's your **go-to test** for validating that any changes haven't broken the system.

## 🚀 Quick Start

### Run the Test
```bash
# From the tests directory
python run_comprehensive_test.py

# Or directly
python test_comprehensive_e2e.py
```

### What It Tests
The test validates **11 critical workflow stages**:

0. **Drop All Existing Tables** 🗑️
   - Removes all existing tables completely
   - Ensures clean slate for testing
   - Mimics fresh database initialization

1. **Database Connection & Schema** ✅
   - Verifies database connectivity
   - Checks all required tables exist
   - Validates table structure and columns

2. **News Collection & Storage** 📰
   - Fetches real news from NewsAPI
   - Verifies articles are stored in database
   - Validates article structure and recent dates

3. **Market Data Collection & Storage** 📊
   - Fetches real market data from yfinance
   - Verifies data is stored in database
   - Validates data structure

4. **NLP Processing & Storage** 🧠
   - Processes articles with NLP (spaCy + FinBERT)
   - Verifies NLP features are stored
   - Validates sentiment and entity extraction

5. **Analysis Generation** 🔍
   - Runs historical and today's analysis
   - Generates trading signals
   - Validates report structure

6. **Report Saving & Database Storage** 💾
   - Saves analysis report to database
   - Verifies all data is stored correctly
   - Validates signal storage

7. **JSON Export Functionality** 📄
   - Exports report to JSON format
   - Saves to file system
   - Validates export structure

8. **API Endpoints Testing** 🔌
   - Tests all API endpoints (if FastAPI server running)
   - Validates response structure
   - Checks data consistency

9. **Test Data Cleanup** 🧹
   - Removes test data from database
   - Ensures clean state for future tests

10. **Complete Staging Database Cleanup** 🗑️
    - Completely empties all tables
    - Resets auto-increment counters
    - Reports database size before/after
    - Ensures pristine staging environment

## 📋 Test Output

### Success Example
```
🚀 STARTING Comprehensive E2E Test
📅 Started at: 2025-08-22 18:30:00
🌍 Environment: staging
🗄️  Database: stockometry_staging
================================================================================

[18:30:01] 🔍 STEP: Database Connection & Schema Initialization
------------------------------------------------------------
✅ Database schema initialized successfully
✅ All required tables exist: ['articles', 'daily_reports', 'predicted_stocks', 'report_signals', 'signal_sources', 'stock_data']
✅ Articles table has all required columns: 15 columns

[18:30:02] 🔍 STEP: News Collection & Storage
------------------------------------------------------------
ℹ️  Cleared existing test data
ℹ️  Fetching news from NewsAPI...
✅ Collected 47 articles
✅ Article structure validation passed
✅ Found 47 recent articles (last 7 days)

... (more steps) ...

🎉 Comprehensive E2E Test COMPLETED SUCCESSFULLY!
⏱️  Total duration: 0:02:15
📊 All workflow stages validated
🗄️  Database state verified at each step
🔌 API endpoints tested
================================================================================
```

### Failure Example
```
[18:30:15] 🔍 STEP: NLP Processing & Storage
------------------------------------------------------------
ℹ️  Processing articles with NLP...
❌ NLP processing test failed: 'NLPProcessor' object has no attribute 'sentiment_pipeline'

💥 Comprehensive E2E Test FAILED!
❌ Error: 'NLPProcessor' object has no attribute 'sentiment_pipeline'
⏱️  Duration before failure: 0:00:15
🔍 Check the step above for details
================================================================================
```

## 🔍 Debugging Failures

### Database Issues
- **Missing tables/columns**: Check `stockometry/database/connection.py`
- **Connection errors**: Verify PostgreSQL is running and credentials are correct

### News Collection Issues
- **No articles collected**: Check NewsAPI key and internet connectivity
- **Article structure errors**: Check `stockometry/core/collectors/news_collector.py`

### NLP Issues
- **Processing failures**: Check `stockometry/core/nlp/processor.py`
- **Model loading errors**: Verify spaCy and FinBERT models are installed

### Analysis Issues
- **Report generation failures**: Check `stockometry/core/analysis/` modules
- **Signal generation errors**: Verify sector mapping and analysis logic

### API Issues
- **Endpoint failures**: Check if FastAPI server is running
- **Response structure errors**: Check `stockometry/api/routes.py`

## 🛠️ Customization

### Test Specific Components
```python
# Test only news collection
test = ComprehensiveE2ETest()
test.check_database_connection()
test.test_news_collection()

# Test only analysis
test = ComprehensiveE2ETest()
test.test_analysis_generation()
```

### Modify Validation Logic
```python
# Add custom validation in any test method
def test_news_collection(self):
    # ... existing code ...
    
    # Add custom checks
    if article_count < 10:
        self.log_error("Expected at least 10 articles")
```

## 📊 Database Validation

The test validates database state at each step:

- **Table existence**: All required tables are present
- **Column structure**: Required columns exist with correct types
- **Data integrity**: Data is stored correctly and completely
- **Relationships**: Foreign key relationships are maintained
- **Cleanup**: Test data is removed after testing

## 🌍 Environment Support

- **Staging**: Uses `stockometry_staging` database
- **Production**: Would use `stockometry` database (when environment is set to "production")
- **Automatic**: Database selection is handled automatically based on settings

## 🎯 When to Run This Test

- **Before deploying changes** to production
- **After modifying core modules** (collectors, analysis, API)
- **When debugging issues** to isolate problems
- **As a smoke test** to verify system health
- **After database schema changes** to ensure compatibility

## 🚨 Important Notes

1. **Uses Staging Database**: Always runs against staging, never production
2. **Real API Calls**: Makes actual calls to NewsAPI and yfinance
3. **Data Cleanup**: Automatically cleans up test data
4. **Complete Database Reset**: Empties all tables and resets counters after testing
5. **Comprehensive Coverage**: Tests the entire workflow end-to-end
6. **Easy Debugging**: Clear step-by-step output with timestamps

## 🗑️ Database Cleanup

### What Gets Cleaned Up
The comprehensive test includes **three levels of cleanup**:

0. **Initial Table Drop (Step 0)**:
   - Drops ALL existing tables completely
   - Ensures clean slate for testing
   - Mimics fresh database initialization
   - Disables foreign key constraints temporarily for clean drops

1. **Test Data Cleanup (Step 9)**:
   - Removes specific test reports and signals
   - Cleans up test articles with test/e2e URLs
   - Removes orphaned data

2. **Complete Database Cleanup (Step 10)**:
   - **Empties ALL tables completely**:
     - `daily_reports` → 0 records
     - `report_signals` → 0 records  
     - `articles` → 0 records
     - `stock_data` → 0 records
     - `predicted_stocks` → 0 records
     - `signal_sources` → 0 records
   - **Resets auto-increment counters** to start from 1
   - **Reports database size** before and after cleanup
   - **Verifies complete cleanup** with record counts

### Why Initial Table Drop?
- **Fresh start** - mimics real-world database initialization
- **No legacy data** - ensures clean testing environment
- **Schema validation** - tests that `init_db()` creates all required tables
- **Dependency testing** - verifies table creation order and constraints
- **Professional testing** - simulates production deployment scenarios

### Why Complete Cleanup?
- **Pristine environment** for each test run
- **No data contamination** between test runs
- **Predictable ID sequences** starting from 1
- **Easy debugging** with clean slate
- **Professional testing standards**

## 🔧 Troubleshooting

### Common Issues
- **Import errors**: Ensure you're in the correct directory
- **Database connection**: Verify PostgreSQL is running
- **API keys**: Check NewsAPI key in settings.yml
- **Dependencies**: Ensure all required packages are installed

### Getting Help
If the test fails:
1. **Read the error message** carefully
2. **Check the step** where it failed
3. **Verify the component** mentioned in the error
4. **Run individual steps** to isolate the issue
5. **Check logs** for additional details

---

**This test is your safety net - run it whenever you make changes to ensure Stockometry continues to work correctly!** 🚀
