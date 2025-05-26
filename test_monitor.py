#!/usr/bin/env python3
"""
Test file for Telegram News Monitor
Demonstrates model validation and basic functionality
"""

import asyncio
from datetime import datetime
from telegram_news_monitor import (
    ChannelConfig,
    TelegramMessage,
    TopicDetectionResult,
    DetectedTopic,
    AppConfig,
    load_config,
)


def test_pydantic_models():
    """Test Pydantic model validation"""
    print("Testing Pydantic Models...")

    # Test ChannelConfig
    try:
        channel = ChannelConfig(
            name="Test Channel", tg_chan_name="test_channel", affiliation="right-wing"
        )
        print(f"✅ ChannelConfig: {channel.name} - {channel.affiliation}")
    except Exception as e:
        print(f"❌ ChannelConfig error: {e}")

    # Test invalid affiliation
    try:
        invalid_channel = ChannelConfig(
            name="Invalid Channel",
            tg_chan_name="invalid",
            affiliation="center",  # Invalid affiliation
        )
        print("❌ Should have failed validation")
    except ValueError as e:
        print(f"✅ Validation caught invalid affiliation: {e}")

    # Test TelegramMessage
    try:
        message = TelegramMessage(
            id=12345,
            text="זוהי הודעת בדיקה על אירועים עכשוויים",  # Hebrew test message
            timestamp=datetime.now(),
            channel_name="Test Channel",
            channel_affiliation="left-wing",
        )
        print(f"✅ TelegramMessage: {message.id} - {len(message.text)} chars")
    except Exception as e:
        print(f"❌ TelegramMessage error: {e}")

    # Test TopicDetectionResult
    try:
        result = TopicDetectionResult(
            has_mutual_topic=True,
            topic_name="רפורמת הפנסיה",  # Hebrew topic name
            confidence_score=0.85,
        )
        print(f"✅ TopicDetectionResult: {result.topic_name}")
    except Exception as e:
        print(f"❌ TopicDetectionResult error: {e}")

    # Test DetectedTopic
    try:
        topic = DetectedTopic(
            topic_id="abc123",
            topic_name="רפורמת הפנסיה",  # Hebrew topic name
            confidence_score=0.85,
        )
        print(f"✅ DetectedTopic: {topic.topic_name} (ID: {topic.topic_id})")
    except Exception as e:
        print(f"❌ DetectedTopic error: {e}")


def test_configuration():
    """Test configuration loading"""
    print("\nTesting Configuration...")

    try:
        config = load_config()
        print(f"✅ Config loaded with {len(config.channels)} channels")
        print(f"   Interval: {config.interval_minutes} minutes")
        print(f"   Model: {config.llm_model}")

        # Check channel balance
        right_wing = sum(1 for c in config.channels if c.affiliation == "right-wing")
        left_wing = sum(1 for c in config.channels if c.affiliation == "left-wing")
        print(f"   Channels: {right_wing} right-wing, {left_wing} left-wing")

        if config.telegram_api_id == 0:
            print("⚠️  Warning: TELEGRAM_API_ID not set")
        if not config.telegram_api_hash:
            print("⚠️  Warning: TELEGRAM_API_HASH not set")

    except Exception as e:
        print(f"❌ Configuration error: {e}")


def test_data_flow():
    """Test data flow simulation"""
    print("\nTesting Data Flow...")

    # Simulate messages from different channels
    messages = [
        TelegramMessage(
            id=1,
            text="חדש: מדיניות אקלים חדשה הוכרזה על ידי גורמים ממשלתיים",  # Hebrew message
            timestamp=datetime.now(),
            channel_name="Right Wing News",
            channel_affiliation="right-wing",
        ),
        TelegramMessage(
            id=2,
            text="עדכון מדיניות אקלים: ארגוני סביבה משבחים את הרגולציות החדשות",  # Hebrew message
            timestamp=datetime.now(),
            channel_name="Left Wing News",
            channel_affiliation="left-wing",
        ),
        TelegramMessage(
            id=3,
            text="מנהיגי עסקים מודאגים מהשפעת הרגולציות החדשות על האקלים",  # Hebrew message
            timestamp=datetime.now(),
            channel_name="Right Wing News",
            channel_affiliation="right-wing",
        ),
    ]

    # Group by affiliation
    right_wing_msgs = [
        m.text for m in messages if m.channel_affiliation == "right-wing"
    ]
    left_wing_msgs = [m.text for m in messages if m.channel_affiliation == "left-wing"]

    print(f"✅ Simulated {len(messages)} messages")
    print(f"   Right-wing: {len(right_wing_msgs)} messages")
    print(f"   Left-wing: {len(left_wing_msgs)} messages")

    # Simulate topic detection result
    detection_result = TopicDetectionResult(
        has_mutual_topic=True,
        topic_name="מדיניות אקלים",  # Hebrew topic name
        confidence_score=0.78,
    )

    # Simulate detected topic with messages
    detected_topic = DetectedTopic(
        topic_id="climate01",
        topic_name="מדיניות אקלים",
        right_wing_messages=[
            msg for msg in messages if msg.channel_affiliation == "right-wing"
        ],
        left_wing_messages=[
            msg for msg in messages if msg.channel_affiliation == "left-wing"
        ],
        confidence_score=0.78,
    )

    print(f"✅ Simulated detection result:")
    print(f"   Topic: {detection_result.topic_name}")
    print(f"   Confidence: {detection_result.confidence_score}")
    print(
        f"   Stored messages: {len(detected_topic.right_wing_messages)} right, {len(detected_topic.left_wing_messages)} left"
    )


if __name__ == "__main__":
    print("🧪 Telegram News Monitor - Test Suite")
    print("=" * 50)

    test_pydantic_models()
    test_configuration()
    test_data_flow()

    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("\nTo run the actual monitor:")
    print("1. Set up your .env file with API credentials")
    print("2. Configure channels in telegram_news_monitor.py")
    print("3. Run: python telegram_news_monitor.py")
