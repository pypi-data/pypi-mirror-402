"""
Example usage of logflow SDK
"""

from logflow import Logger
import time

def example_basic():
    """Basic usage example"""
    print("=== Basic Usage ===")
    
    logger = Logger(
        api_key="test_api_key",
        project_id="test_project_id",
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
    
    # Wait a moment
    time.sleep(1)
    
    # Close logger
    logger.close()


def example_context_manager():
    """Context manager example"""
    print("\n=== Context Manager ===")
    
    with Logger(
        api_key="test_api_key",
        project_id="test_project_id",
        debug=True
    ) as logger:
        logger.log(
            bucket="errors",
            data={
                "error": "Something went wrong",
                "code": 500
            }
        )
    # Automatically closes and flushes


def example_multiple_logs():
    """Multiple logs example"""
    print("\n=== Multiple Logs ===")
    
    with Logger(
        api_key="test_api_key",
        project_id="test_project_id",
        batch_size=5,
        debug=True
    ) as logger:
        # Send multiple logs
        for i in range(10):
            logger.log(
                bucket="datacapture",
                data={
                    "event": "api_call",
                    "endpoint": f"/api/users/{i}",
                    "status": 200,
                    "duration_ms": 150 + i
                }
            )
            time.sleep(0.1)


if __name__ == "__main__":
    example_basic()
    example_context_manager()
    example_multiple_logs()
    
    print("\n✅ All examples completed!")
