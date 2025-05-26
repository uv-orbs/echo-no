import asyncio
import platform
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from collections import defaultdict
import os
import uuid
from dataclasses import dataclass

from pydantic import BaseModel, Field, validator
from pydantic_ai import Agent, RunContext
from telethon import TelegramClient, events
from telethon.tl.types import Message
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


# Pydantic Models
class ChannelConfig(BaseModel):
    """Configuration for a Telegram channel"""

    name: str = Field(..., description="Human-readable name of the channel")
    username: str = Field(..., description="Telegram username (without @)")
    affiliation: str = Field(
        ..., description="Political affiliation: 'right-wing' or 'left-wing'"
    )

    @validator("affiliation")
    def validate_affiliation(cls, v):
        if v not in ["right-wing", "left-wing"]:
            raise ValueError('Affiliation must be either "right-wing" or "left-wing"')
        return v


class TelegramMessage(BaseModel):
    """Structured representation of a Telegram message"""

    id: int
    text: str
    timestamp: datetime
    channel_name: str
    channel_affiliation: str


class TopicDetectionResult(BaseModel):
    """Result of topic detection analysis"""

    has_mutual_topic: bool = Field(..., description="Whether a mutual topic was found")
    topic_name: Optional[str] = Field(
        None, description="Brief name/identifier for the topic in Hebrew"
    )
    confidence_score: Optional[float] = Field(
        None, description="Confidence in the topic detection (0-1)"
    )


class DetectedTopic(BaseModel):
    """A detected mutual topic with associated messages"""

    topic_id: str = Field(..., description="Unique identifier for the topic")
    topic_name: str = Field(..., description="Brief name for the topic")
    right_wing_messages: List[TelegramMessage] = Field(default_factory=list)
    left_wing_messages: List[TelegramMessage] = Field(default_factory=list)
    first_detected: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    confidence_score: float = Field(..., description="Detection confidence")


class AppConfig(BaseModel):
    """Application configuration"""

    telegram_api_id: int
    telegram_api_hash: str
    channels: List[ChannelConfig]
    interval_minutes: int = Field(
        default=5, description="Monitoring interval in minutes"
    )
    llm_model: str = Field(
        default="groq:llama3-groq-70b-8192-tool-use-preview",
        description="LLM model to use",
    )
    max_messages_per_check: int = Field(
        default=50, description="Maximum messages to fetch per channel per check"
    )


# Global configuration
def load_config() -> AppConfig:
    """Load configuration from environment variables and defaults"""

    # Default channels for testing - replace with actual channel usernames
    default_channels = [
        ChannelConfig(
            name="Right Wing News 1",
            username="rightwing_news_1",  # Replace with actual username
            affiliation="right-wing",
        ),
        ChannelConfig(
            name="Right Wing News 2",
            username="rightwing_news_2",  # Replace with actual username
            affiliation="right-wing",
        ),
        ChannelConfig(
            name="Left Wing News 1",
            username="leftwing_news_1",  # Replace with actual username
            affiliation="left-wing",
        ),
        ChannelConfig(
            name="Left Wing News 2",
            username="leftwing_news_2",  # Replace with actual username
            affiliation="left-wing",
        ),
    ]

    return AppConfig(
        telegram_api_id=int(os.getenv("TELEGRAM_API_ID", "0")),
        telegram_api_hash=os.getenv("TELEGRAM_API_HASH", ""),
        channels=default_channels,
        interval_minutes=int(os.getenv("INTERVAL_MINUTES", "5")),
        llm_model=os.getenv("LLM_MODEL", "groq:llama3-groq-70b-8192-tool-use-preview"),
        max_messages_per_check=int(os.getenv("MAX_MESSAGES_PER_CHECK", "50")),
    )


class TelegramNewsMonitor:
    """Main class for monitoring Telegram news channels"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.client = None
        self.last_check_time = datetime.now() - timedelta(
            hours=1
        )  # Start with 1 hour ago
        self.topic_detection_agent = self._create_topic_detection_agent()
        self.detected_topics: Dict[str, DetectedTopic] = {}  # topic_id -> DetectedTopic

    def _create_topic_detection_agent(self) -> Agent:
        """Create PydanticAI agent for topic detection only"""

        system_prompt = """
        אתה מומחה לזיהוי נושאים בחדשות. המשימה שלך פשוטה:

        1. קבל הודעות מערוצי חדשות של ימין ושמאל
        2. זהה אם יש נושא אחד ספציפי שנדון על ידי שני הצדדים
        3. אם כן, תן לנושא שם קצר ותמציתי בעברית

        הנחיות:
        - נושא משותף = אותו נושא/אירוע/נושא חדשותי שמוזכר בשני הצדדים
        - שם הנושא צריך להיות קצר (2-4 מילים) ותמציתי
        - החזר has_mutual_topic=True רק אם אתה בטוח ב-80%+ ששני הצדדים דנים באותו נושא
        - אל תנתח או תסכם - רק זהה וקרא לנושא

        דוגמאות לשמות נושאים טובים:
        - "חוק השופטים"
        - "מלחמה בעזה" 
        - "תקציב המדינה"
        - "רפורמת הפנסיה"
        """

        return Agent(
            model=self.config.llm_model,
            result_type=TopicDetectionResult,
            system_prompt=system_prompt,
        )

    async def initialize(self):
        """Initialize Telegram client"""
        try:
            self.client = TelegramClient(
                "news_monitor_session",
                self.config.telegram_api_id,
                self.config.telegram_api_hash,
            )
            await self.client.start()
            logger.info("Telegram client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            raise

    async def fetch_recent_messages(self) -> List[TelegramMessage]:
        """Fetch recent messages from all configured channels"""
        all_messages = []

        for channel in self.config.channels:
            try:
                logger.info(
                    f"Fetching messages from {channel.name} (@{channel.username})"
                )

                # Get the channel entity
                entity = await self.client.get_entity(channel.username)

                # Fetch recent messages
                messages = await self.client.get_messages(
                    entity, limit=self.config.max_messages_per_check
                )

                # Filter messages since last check and convert to our model
                for msg in messages:
                    if (
                        msg.date > self.last_check_time
                        and msg.text
                        and len(msg.text.strip()) > 10
                    ):  # Filter out very short messages

                        telegram_msg = TelegramMessage(
                            id=msg.id,
                            text=msg.text,
                            timestamp=msg.date,
                            channel_name=channel.name,
                            channel_affiliation=channel.affiliation,
                        )
                        all_messages.append(telegram_msg)

                logger.info(
                    f"Fetched {len([m for m in all_messages if m.channel_name == channel.name])} new messages from {channel.name}"
                )

            except Exception as e:
                logger.error(f"Error fetching messages from {channel.name}: {e}")
                continue

        return all_messages

    async def detect_mutual_topics(
        self, messages: List[TelegramMessage]
    ) -> Optional[str]:
        """Detect mutual topics and store messages by topic"""
        if not messages:
            logger.info("No messages to analyze")
            return None

        # Group messages by political affiliation
        right_wing_msgs = [
            msg for msg in messages if msg.channel_affiliation == "right-wing"
        ]
        left_wing_msgs = [
            msg for msg in messages if msg.channel_affiliation == "left-wing"
        ]

        if not right_wing_msgs or not left_wing_msgs:
            logger.info(
                "Need messages from both right-wing and left-wing channels for analysis"
            )
            return None

        logger.info(
            f"Detecting topics in {len(right_wing_msgs)} right-wing and {len(left_wing_msgs)} left-wing messages"
        )

        try:
            # Run topic detection
            result = await self.topic_detection_agent.run(
                f"""
                זהה נושא משותף בהודעות הללו:
                
                הודעות ימין:
                {chr(10).join(f"- {msg.text}" for msg in right_wing_msgs[:10])}
                
                הודעות שמאל:
                {chr(10).join(f"- {msg.text}" for msg in left_wing_msgs[:10])}
                
                האם יש נושא אחד שנדון בשני הצדדים? אם כן, תן לו שם קצר בעברית.
                """
            )

            detection_result = result.data

            if detection_result.has_mutual_topic and detection_result.topic_name:
                # Create or update topic
                topic_id = self._get_or_create_topic_id(detection_result.topic_name)

                if topic_id in self.detected_topics:
                    # Update existing topic
                    topic = self.detected_topics[topic_id]
                    topic.right_wing_messages.extend(right_wing_msgs)
                    topic.left_wing_messages.extend(left_wing_msgs)
                    topic.last_updated = datetime.now()
                    logger.info(
                        f"Updated existing topic: {topic.topic_name} (ID: {topic_id})"
                    )
                else:
                    # Create new topic
                    topic = DetectedTopic(
                        topic_id=topic_id,
                        topic_name=detection_result.topic_name,
                        right_wing_messages=right_wing_msgs,
                        left_wing_messages=left_wing_msgs,
                        confidence_score=detection_result.confidence_score or 0.8,
                    )
                    self.detected_topics[topic_id] = topic
                    logger.info(
                        f"Detected new topic: {topic.topic_name} (ID: {topic_id})"
                    )

                return topic_id
            else:
                logger.info("No mutual topic detected")
                return None

        except Exception as e:
            logger.error(f"Error during topic detection: {e}")
            return None

    def _get_or_create_topic_id(self, topic_name: str) -> str:
        """Get existing topic ID or create new one based on topic name"""
        # Check if we already have a similar topic
        for topic_id, topic in self.detected_topics.items():
            if topic.topic_name.lower() == topic_name.lower():
                return topic_id

        # Create new topic ID
        return str(uuid.uuid4())[:8]  # Short UUID

    def get_topic_data(self, topic_id: str) -> Optional[DetectedTopic]:
        """Get topic data for external processing (e.g., summarization)"""
        return self.detected_topics.get(topic_id)

    def get_all_topics(self) -> Dict[str, DetectedTopic]:
        """Get all detected topics"""
        return self.detected_topics.copy()

    def clear_old_topics(self, hours_old: int = 24):
        """Clear topics older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        topics_to_remove = [
            topic_id
            for topic_id, topic in self.detected_topics.items()
            if topic.last_updated < cutoff_time
        ]

        for topic_id in topics_to_remove:
            removed_topic = self.detected_topics.pop(topic_id)
            logger.info(
                f"Removed old topic: {removed_topic.topic_name} (ID: {topic_id})"
            )

        return len(topics_to_remove)

    def display_topic_detection(self, topic_id: Optional[str]):
        """Display topic detection results"""
        if topic_id and topic_id in self.detected_topics:
            topic = self.detected_topics[topic_id]
            print("\n" + "=" * 80)
            print("🔥 MUTUAL TOPIC DETECTED 🔥")
            print("=" * 80)
            print(f"📋 Topic ID: {topic.topic_id}")
            print(f"📰 Topic Name: {topic.topic_name}")
            print(f"➡️  Right-wing messages: {len(topic.right_wing_messages)}")
            print(f"⬅️  Left-wing messages: {len(topic.left_wing_messages)}")
            print(f"🎯 Confidence: {topic.confidence_score:.2f}")
            print(f"🕐 First detected: {topic.first_detected.strftime('%H:%M:%S')}")
            print(f"🕐 Last updated: {topic.last_updated.strftime('%H:%M:%S')}")
            print("=" * 80)

            # Log the result
            logger.info(f"Topic detected/updated: {topic.topic_name} (ID: {topic_id})")
        else:
            print(
                f"⏰ {datetime.now().strftime('%H:%M:%S')} - No mutual topics found in recent messages"
            )
            logger.info("No mutual topics identified in current analysis")

    def display_topics_summary(self):
        """Display summary of all detected topics"""
        if not self.detected_topics:
            print("📊 No topics detected yet")
            return

        print(f"\n📊 TOPICS SUMMARY ({len(self.detected_topics)} topics)")
        print("-" * 60)
        for topic_id, topic in self.detected_topics.items():
            total_messages = len(topic.right_wing_messages) + len(
                topic.left_wing_messages
            )
            print(f"🏷️  {topic.topic_name} (ID: {topic_id})")
            print(
                f"   📊 {total_messages} messages ({len(topic.right_wing_messages)} right, {len(topic.left_wing_messages)} left)"
            )
            print(f"   🕐 Last updated: {topic.last_updated.strftime('%H:%M:%S')}")
            print()

    async def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        try:
            # Fetch recent messages
            messages = await self.fetch_recent_messages()

            # Update last check time
            self.last_check_time = datetime.now()

            if not messages:
                logger.info("No new messages found")
                # Still show summary if we have topics
                if self.detected_topics:
                    self.display_topics_summary()
                return

            # Detect mutual topics
            topic_id = await self.detect_mutual_topics(messages)

            # Display results
            self.display_topic_detection(topic_id)

            # Show summary every few cycles
            if len(self.detected_topics) > 0:
                self.display_topics_summary()

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")

    async def start_monitoring(self):
        """Start the continuous monitoring loop"""
        logger.info(
            f"Starting news monitoring with {len(self.config.channels)} channels"
        )
        logger.info(f"Monitoring interval: {self.config.interval_minutes} minutes")

        print(f"🚀 Starting Telegram News Monitor")
        print(f"📺 Monitoring {len(self.config.channels)} channels:")
        for channel in self.config.channels:
            print(f"   - {channel.name} (@{channel.username}) [{channel.affiliation}]")
        print(f"⏱️  Check interval: {self.config.interval_minutes} minutes")
        print(f"🤖 Using model: {self.config.llm_model}")
        print("-" * 60)

        while True:
            try:
                await self.run_monitoring_cycle()

                # Wait for the next cycle
                await asyncio.sleep(self.config.interval_minutes * 60)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(30)

    async def cleanup(self):
        """Clean up resources"""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram client disconnected")


async def main():
    """Main function"""
    try:
        # Load configuration
        config = load_config()

        # Validate configuration
        if not config.telegram_api_id or not config.telegram_api_hash:
            logger.error(
                "Telegram API credentials not found. Please set TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables."
            )
            return

        # Create and initialize monitor
        monitor = TelegramNewsMonitor(config)
        await monitor.initialize()

        # Start monitoring
        await monitor.start_monitoring()

    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if "monitor" in locals():
            await monitor.cleanup()


# Platform-specific execution
if __name__ == "__main__":
    if platform.system() == "Emscripten":
        # For Pyodide compatibility
        asyncio.ensure_future(main())
    else:
        # Standard execution
        asyncio.run(main())
