# ECHO-NO
## Telegram News Monitor with PydanticAI

A Python program that monitors Telegram news channels across political affiliations (right-wing and left-wing) to identify mutual topics being discussed by both sides. Uses PydanticAI framework for AI-powered topic analysis and Telethon for Telegram integration.

## Features

- 🔍 **Multi-Channel Monitoring**: Monitor multiple Telegram channels simultaneously
- 🎯 **Topic Detection**: AI-powered identification of mutual topics across political divides
- 📊 **Perspective Analysis**: Summarizes how each side (right-wing vs left-wing) discusses topics
- ⚡ **Real-time Processing**: Configurable monitoring intervals
- 🛡️ **Type Safety**: Full Pydantic validation for data integrity
- 🔄 **Async Architecture**: Non-blocking execution for efficient channel monitoring
- 📝 **Comprehensive Logging**: Detailed logging for monitoring and debugging

## Requirements

- Python 3.8+
- Telegram API credentials
- LLM API access (Groq, OpenAI, etc.)
- Active Telegram channels to monitor

## Installation

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Telegram API credentials**:
   - Go to https://my.telegram.org/apps
   - Create a new application
   - Note down your `api_id` and `api_hash`

4. **Get LLM API access**:
   - For Groq: Sign up at https://console.groq.com/
   - For OpenAI: Sign up at https://platform.openai.com/

5. **Configure environment variables**:
   ```bash
   cp config_template.env .env
   # Edit .env with your actual credentials
   ```

## Configuration

### Environment Variables

Copy `config_template.env` to `.env` and fill in your credentials:

```env
# Telegram API Credentials
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here

# Monitoring Configuration
INTERVAL_MINUTES=5
MAX_MESSAGES_PER_CHECK=50

# LLM Configuration
LLM_MODEL=groq:llama3-groq-70b-8192-tool-use-preview
GROQ_API_KEY=your_groq_api_key_here
```

### Channel Configuration

Edit the `load_config()` function in `telegram_news_monitor.py` to specify your channels:

```python
default_channels = [
    ChannelConfig(
        name="Fox News",
        username="foxnews",  # Telegram username without @
        affiliation="right-wing"
    ),
    ChannelConfig(
        name="CNN",
        username="cnn",
        affiliation="left-wing"
    ),
    # Add more channels...
]
```

## Usage

### Basic Usage

```bash
python telegram_news_monitor.py
```

### Example Output

When a mutual topic is detected:

```
================================================================================
🔥 MUTUAL TOPIC DETECTED 🔥
================================================================================
📰 Headline: שני הצדדים דנים בחקיקת מדיניות אקלים חדשה שעברה בכנסת.
➡️  Right-wing perspective: מבקרים טוענים שהמדיניות כופה רגולציות מוגזמות שיפגעו בעסקים ויעלו עלויות לצרכנים.
⬅️  Left-wing perspective: תומכים טוענים שהמדיניות חיונית להגנת הסביבה ותיצור מקומות עבודה ירוקים.
🎯 Confidence: 0.85
================================================================================
```

When no mutual topics are found:
```
⏰ 14:30:15 - No mutual topics found in recent messages
```

## Program Structure

### Core Components

1. **Data Models** (`Pydantic`):
   - `ChannelConfig`: Channel configuration with political affiliation
   - `TelegramMessage`: Structured message representation
   - `TopicResult`: AI analysis results
   - `AppConfig`: Application configuration

2. **Telegram Integration** (`Telethon`):
   - Async message fetching from multiple channels
   - Rate limiting and error handling
   - Message filtering and deduplication

3. **AI Analysis** (`PydanticAI`):
   - Topic identification across political divides
   - Perspective summarization
   - Confidence scoring

4. **Monitoring Loop**:
   - Configurable check intervals
   - Continuous monitoring with error recovery
   - Graceful shutdown handling

### Key Classes

- `TelegramNewsMonitor`: Main monitoring class
- `ChannelConfig`: Channel configuration model
- `TopicResult`: Analysis result structure

## Advanced Configuration

### Custom LLM Models

The program supports various LLM providers through PydanticAI:

```python
# Groq models
LLM_MODEL=groq:llama3-groq-70b-8192-tool-use-preview

# OpenAI models
LLM_MODEL=openai:gpt-4

# Other providers supported by PydanticAI
```

### Monitoring Parameters

Adjust monitoring behavior via environment variables:

- `INTERVAL_MINUTES`: How often to check for new messages (default: 5)
- `MAX_MESSAGES_PER_CHECK`: Maximum messages to fetch per channel (default: 50)

### Channel Selection

Choose channels based on:
- **Activity Level**: Channels with regular posting
- **Content Quality**: Channels with substantial news content
- **Political Balance**: Equal representation of perspectives

## Error Handling

The program includes comprehensive error handling:

- **Telegram API Errors**: Rate limiting, authentication issues
- **Network Issues**: Connection timeouts, retries
- **LLM API Errors**: Model unavailability, quota limits
- **Data Validation**: Pydantic model validation

## Logging

Detailed logging is provided for:
- Channel monitoring status
- Message fetch statistics
- Topic analysis results
- Error conditions and recovery

## Platform Compatibility

The program is designed for:
- **Standard Python**: Full functionality
- **Pyodide**: Browser-based execution (limited network access)

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black telegram_news_monitor.py
```

### Type Checking

```bash
mypy telegram_news_monitor.py
```

## Limitations

1. **Telegram Rate Limits**: Respect Telegram's API rate limits
2. **Channel Access**: Can only monitor public channels or channels you have access to
3. **Language Support**: Currently optimized for English content
4. **Topic Complexity**: AI analysis quality depends on message content and LLM capabilities

## Security Considerations

- Store API credentials securely in environment variables
- Never commit `.env` files to version control
- Use read-only Telegram API access when possible
- Monitor API usage to avoid quota exhaustion

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify Telegram API credentials
   - Ensure phone number verification if required

2. **Channel Access Issues**:
   - Verify channel usernames are correct
   - Ensure channels are public or you have access

3. **LLM API Errors**:
   - Check API key validity
   - Verify quota availability
   - Try alternative models

4. **No Topics Detected**:
   - Increase monitoring interval
   - Check if channels are actively posting
   - Verify message content quality

### Debug Mode

Enable debug logging:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Follow the existing code structure
2. Add type hints for all functions
3. Include comprehensive error handling
4. Write tests for new functionality
5. Update documentation

## License

This project is provided as-is for educational and research purposes. Ensure compliance with Telegram's Terms of Service and applicable laws when using this software.

## Disclaimer

This tool is for monitoring public information only. Users are responsible for:
- Complying with Telegram's Terms of Service
- Respecting channel owners' rights
- Using the tool ethically and legally
- Ensuring appropriate use of AI analysis results

The analysis results are AI-generated and should be verified independently for accuracy. 