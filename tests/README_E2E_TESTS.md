# Stockometry E2E Test Suite

This directory contains comprehensive end-to-end tests for the Stockometry stock analysis bot. These tests validate the entire pipeline from news data ingestion to final report generation.

## 🎯 Test Scenarios

### 1. **test_e2e_bullish_tech.py** - Bullish Technology Sector
- **Purpose**: Tests strong bullish signals for technology sector
- **Data**: 6 days of positive sentiment + high-impact positive news today
- **Expected**: Historical bullish signal + impact signal + confidence signal
- **Stocks**: AAPL, MSFT, NVDA with specific news events

### 2. **test_e2e_bearish_financial.py** - Bearish Financial Sector
- **Purpose**: Tests strong bearish signals for financial sector
- **Data**: 6 days of negative sentiment + high-impact negative news today
- **Expected**: Historical bearish signal + impact signal + confidence signal
- **Stocks**: GS with regulatory investigation news

### 3. **test_e2e_mixed_signals.py** - Mixed Market Signals
- **Purpose**: Tests multiple sectors with different sentiment patterns
- **Data**: 
  - Technology: 6 days bullish + positive impact today
  - Healthcare: 6 days bearish + negative impact today
  - Energy: 6 days neutral + neutral impact today
- **Expected**: Multiple historical signals + impact signals + potential confidence signals

### 4. **test_e2e_edge_cases.py** - Edge Cases and No-Signals
- **Purpose**: Tests scenarios that should NOT generate signals
- **Data**:
  - Insufficient historical data (only 2 days)
  - Mixed sentiment over 6 days
  - Weak sentiment scores (0.55-0.60)
  - No high-impact news today
  - Articles without sector classification
- **Expected**: Minimal or no signals generated

### 5. **test_e2e.py** - Original E2E Test
- **Purpose**: Original comprehensive test with mixed scenarios
- **Data**: Technology bullish trend + various noise articles
- **Expected**: Technology confidence signal with MSFT prediction

## 🚀 Running the Tests

### Individual Tests
```bash
# Run specific test scenarios
python -m tests.test_e2e_bullish_tech
python -m tests.test_e2e_bearish_financial
python -m tests.test_e2e_mixed_signals
python -m tests.test_e2e_edge_cases
python -m tests.test_e2e
```

### All Tests at Once
```bash
# Run the complete test suite
python -m tests.run_all_e2e_tests
```

### Test Runner Features
- **Parallel Execution**: Each test runs independently
- **Comprehensive Reporting**: Success/failure status with timing
- **Summary Statistics**: Pass rate, total time, individual test results
- **Error Details**: Full error information for failed tests

## 🏗️ Test Architecture

### Database Strategy
- **Staging Database**: Uses `stockometry_staging` for clean testing
- **Isolated Environment**: Each test creates/destroys its own schema
- **No Production Impact**: Completely separate from main database

### Data Structure
Each test creates realistic fake news articles with:
- **Proper NLP Features**: Sentiment scores, entity recognition
- **Realistic Timestamps**: 6 days of historical + today's news
- **Sector Classification**: Proper sector entities for analysis
- **Stock Symbols**: Company names and ticker symbols
- **Sentiment Patterns**: Designed to trigger specific signal types

### Test Flow
1. **Setup**: Create staging database tables and insert test data
2. **Execution**: Run the full analysis pipeline
3. **Verification**: Check JSON output and database records
4. **Cleanup**: Remove test data and restore clean state

## 📊 Expected Output Structure

### JSON Report Format
```json
{
  "report_id": 1,
  "report_date": "2025-08-22",
  "generated_at_utc": "2025-08-22T04:30:34.896670",
  "executive_summary": "A consistent bullish trend was observed...",
  "signals": {
    "historical": [
      {
        "type": "HISTORICAL",
        "direction": "Bullish",
        "sector": "Technology",
        "source_articles": [...]
      }
    ],
    "impact": [
      {
        "type": "IMPACT",
        "sector": "Technology",
        "direction": "UP",
        "details": "High-impact news...",
        "source_articles": [...]
      }
    ],
    "confidence": [
      {
        "type": "CONFIDENCE",
        "direction": "BULLISH",
        "sector": "Technology",
        "predicted_stocks": [
          {
            "symbol": "MSFT",
            "reason": "Microsoft AI Breakthrough",
            "url": "https://...",
            "score": 0.98
          }
        ],
        "source_articles": [...]
      }
    ]
  }
}
```

## 🔍 What Each Test Validates

### Signal Generation Logic
- **Historical Signals**: 6+ days of consistent sentiment
- **Impact Signals**: High-impact news with strong sentiment
- **Confidence Signals**: Alignment between historical and impact

### Data Processing
- **NLP Features**: Sentiment analysis and entity extraction
- **Sector Classification**: Proper sector identification
- **Stock Prediction**: Company-specific predictions with reasons

### Output Generation
- **JSON Structure**: Correct format per EXAMPLE.md
- **Database Storage**: Proper record creation and relationships
- **Executive Summary**: Human-readable analysis summary

### Edge Case Handling
- **Insufficient Data**: No signals when <6 days available
- **Mixed Sentiment**: No clear directional signals
- **Weak Sentiment**: Threshold-based filtering
- **Missing Sectors**: Graceful handling of unclassified content

## 🧪 Testing Best Practices

### Before Running Tests
1. **Database Setup**: Ensure `stockometry_staging` database exists
2. **Environment**: Activate virtual environment with all dependencies
3. **Clean State**: No existing test data in staging database

### During Test Execution
1. **Monitor Output**: Watch for setup/execution/verification phases
2. **Check Timing**: Note execution time for performance monitoring
3. **Review Errors**: Full error details are provided for debugging

### After Test Completion
1. **Review Results**: Check pass/fail status and timing
2. **Analyze Failures**: Use error details to identify issues
3. **Clean Up**: Tests automatically clean up, but verify staging DB

## 🐛 Troubleshooting

### Common Issues
- **Database Connection**: Ensure PostgreSQL is running and accessible
- **Missing Dependencies**: Install all requirements from `requirements.txt`
- **Permission Issues**: Check database user permissions for staging DB
- **Import Errors**: Ensure Python path includes project root

### Debug Mode
Each test provides detailed logging:
- Setup phase with database operations
- Execution phase with analysis pipeline
- Verification phase with result checking
- Cleanup phase with data removal

### Manual Verification
If tests fail, you can manually inspect:
- Staging database contents
- Generated JSON files
- Analysis pipeline logs
- Database table structures

## 📈 Performance Metrics

### Expected Timings
- **Individual Tests**: 5-15 seconds each
- **Full Suite**: 30-60 seconds total
- **Database Operations**: 2-5 seconds per test
- **Analysis Pipeline**: 3-10 seconds per test

### Optimization Tips
- **Parallel Execution**: Tests can run independently
- **Database Indexing**: Ensure proper indexes on staging DB
- **Memory Usage**: Monitor during large test data scenarios
- **Cleanup Efficiency**: Tests automatically clean up resources

## 🔄 Continuous Integration

### Automated Testing
These tests are designed for:
- **CI/CD Pipelines**: Automated validation of changes
- **Pre-deployment**: Verify system before production
- **Regression Testing**: Ensure new features don't break existing functionality
- **Performance Monitoring**: Track execution time trends

### Test Maintenance
- **Data Updates**: Refresh test data periodically for realism
- **Scenario Expansion**: Add new market scenarios as needed
- **Threshold Tuning**: Adjust sentiment thresholds based on real-world data
- **Coverage Analysis**: Ensure all code paths are tested

---

## 🎯 Quick Start

```bash
# 1. Ensure staging database exists
# 2. Activate virtual environment
# 3. Run all tests
python -m tests.run_all_e2e_tests

# Or run individual tests
python -m tests.test_e2e_bullish_tech
```

This test suite provides comprehensive validation of the Stockometry system before using real API calls, ensuring reliability and correctness of the analysis pipeline.
