"""
Example usage of logflow SDK
"""

from logflow import Logger
import time

def example_basic():
    """Basic usage example - super simple!"""
    print("=== Basic Usage ===")
    
    # Just create logger with API key - that's it!
    logger = Logger(
        api_key="test_api_key",
        debug=True
    )
    
    # Send a log
    logger.log(
        bucket="user_activity",
        data={
            "event": "profile_view",
            "user_id": "123",
            "profile_id": "456"
        }
    )
    
    # Wait a moment to see logs being sent
    time.sleep(1)
    
    # No need to close - cleanup happens automatically!
    print("✅ Log sent! Cleanup will happen automatically on exit.")


def example_multiple_logs():
    """Multiple logs example"""
    print("\n=== Multiple Logs ===")
    
    logger = Logger(
        api_key="test_api_key",
        batch_size=5,
        debug=True
    )
    
    # Send multiple logs
    for i in range(10):
        logger.log(
            bucket="api_calls",
            data={
                "event": "api_call",
                "endpoint": f"/api/users/{i}",
                "status": 200,
                "duration_ms": 150 + i
            }
        )
        time.sleep(0.1)
    
    print("✅ All logs queued! They'll be sent automatically.")


def example_error_logging():
    """Error logging example"""
    print("\n=== Error Logging ===")
    
    logger = Logger(api_key="test_api_key", debug=True)
    
    try:
        # Simulate an error
        result = 1 / 0
    except Exception as e:
        logger.log(
            bucket="errors",
            data={
                "error": str(e),
                "type": type(e).__name__,
                "context": "division_operation"
            }
        )
        print("✅ Error logged!")


if __name__ == "__main__":
    example_basic()
    example_multiple_logs()
    example_error_logging()
    
    print("\n✅ All examples completed!")
    print("⏳ Waiting 2 seconds for background logs to flush...")
    time.sleep(2)
    print("✨ Done! All logs sent.")
