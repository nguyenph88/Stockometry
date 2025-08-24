#!/usr/bin/env python3
"""
Test script for Scheduler Docker

This script tests the Scheduler Docker functionality without requiring
the full FastAPI application to be running.
"""

import sys
import os
import time
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from stockometry.scheduler_docker.scheduler_docker import SchedulerDocker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scheduler_docker():
    """Test the Scheduler Docker functionality"""
    logger.info("Testing Scheduler Docker...")
    
    # Create scheduler instance
    scheduler = SchedulerDocker()
    
    try:
        # Test 1: Check initial status
        logger.info("Test 1: Checking initial status...")
        status = scheduler.get_status()
        logger.info(f"Initial status: {status}")
        assert status["status"] == "stopped", "Scheduler should be stopped initially"
        
        # Test 2: Start scheduler
        logger.info("Test 2: Starting scheduler...")
        start_result = scheduler.start()
        logger.info(f"Start result: {start_result}")
        assert start_result["status"] == "started", "Scheduler should start successfully"
        
        # Test 3: Check running status
        logger.info("Test 3: Checking running status...")
        time.sleep(2)  # Give scheduler time to start
        status = scheduler.get_status()
        logger.info(f"Running status: {status}")
        assert status["status"] == "running", "Scheduler should be running"
        assert status["running"] == True, "Scheduler should be marked as running"
        
        # Test 4: Check jobs
        logger.info("Test 4: Checking scheduled jobs...")
        assert status["total_jobs"] > 0, "Scheduler should have jobs"
        logger.info(f"Total jobs: {status['total_jobs']}")
        for job in status.get("jobs", []):
            logger.info(f"Job: {job['id']} - {job['name']} - Next run: {job['next_run']}")
        
        # Test 5: Check if running
        logger.info("Test 5: Checking is_running method...")
        is_running = scheduler.is_running()
        logger.info(f"Is running: {is_running}")
        assert is_running == True, "is_running should return True"
        
        # Test 6: Stop scheduler
        logger.info("Test 6: Stopping scheduler...")
        stop_result = scheduler.stop()
        logger.info(f"Stop result: {stop_result}")
        assert stop_result["status"] == "stopped", "Scheduler should stop successfully"
        
        # Test 7: Check final status
        logger.info("Test 7: Checking final status...")
        time.sleep(1)  # Give scheduler time to stop
        status = scheduler.get_status()
        logger.info(f"Final status: {status}")
        assert status["status"] == "stopped", "Scheduler should be stopped"
        assert status["running"] == False, "Scheduler should not be running"
        
        logger.info("✅ All tests passed! Scheduler Docker is working correctly.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise
    finally:
        # Ensure scheduler is stopped
        try:
            if scheduler.is_running():
                scheduler.stop()
                logger.info("Scheduler stopped in cleanup")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

def test_scheduler_restart():
    """Test scheduler restart functionality"""
    logger.info("Testing scheduler restart...")
    
    scheduler = SchedulerDocker()
    
    try:
        # Start scheduler
        scheduler.start()
        time.sleep(1)
        
        # Test restart
        restart_result = scheduler.restart()
        logger.info(f"Restart result: {restart_result}")
        assert restart_result["status"] == "started", "Restart should succeed"
        
        # Verify it's running
        assert scheduler.is_running(), "Scheduler should be running after restart"
        
        logger.info("✅ Restart test passed!")
        
    except Exception as e:
        logger.error(f"❌ Restart test failed: {str(e)}")
        raise
    finally:
        scheduler.stop()

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting Scheduler Docker Tests...")
        
        # Run basic functionality test
        test_scheduler_docker()
        
        # Run restart test
        test_scheduler_restart()
        
        logger.info("🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Test suite failed: {str(e)}")
        sys.exit(1)
