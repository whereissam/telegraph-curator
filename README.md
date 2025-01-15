# Telegraph Curator

📚 A robust tool for collecting and organizing Telegram channel and group content with structured outputs and media archiving capabilities.

## Overview

Telegraph Curator helps you systematically collect and organize content from Telegram channels and groups. It generates structured markdown reports and organizes media content, making it perfect for content archiving, research, and analysis.

## Features

- 📱 Monitor multiple Telegram channels and groups
- 📊 Collect comprehensive message metadata
- 🗂️ Organize media content systematically
- 📝 Generate structured markdown reports
- 🔗 Parse message entities (URLs, mentions)
- ⏰ Configurable time-based collection
- 🔒 Privacy-focused configuration

## Prerequisites

- Python 3.7 or higher
- Telegram API credentials
  - API ID
  - API Hash
- Python packages listed in `requirements.txt`

## Installation

1. Clone the repository
```bash
git clone https://github.com/whereissam/telegraph-curator.git
cd telegraph-curator
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up configuration
```bash
cp .env.example .env
```

## Configuration

### Environment Setup

Create a `.env` file with your Telegram API credentials:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

### Channel/Group Configuration

Create `config.py` to specify your sources:
```python
CHANNELS = [
    '@example_channel',
    '@another_channel'
]

GROUPS = [
    '@example_group'
]
```

## Usage

### Channel Content Collection
```bash
python telegram_channel_reader.py
```

### Group Content Collection
```bash
python telegram_group_reader.py
```

### Output Structure

#### Message Data
- Timestamp
- Sender information
- Message content
- View/forward counts
- Links and mentions
- Media references

#### Generated Files
- `telegram_messages_[DATE].md`: Structured message report
- `/telegram_media/`: Media file directory
- `/telegram_group_media/`: Group media directory

## Responsible Usage Guidelines

- Respect Telegram's Terms of Service
- Implement appropriate rate limiting
- Handle data responsibly
- Consider bandwidth and storage constraints
- Respect user privacy

## Development

### File Structure
```
telegraph-curator/
├── telegram_channel_reader.py
├── telegram_group_reader.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Configuration Files
```
# .gitignore
config.py
.env
*session*
telegram_media/*
telegram_group_media/*
*.md
```

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Telethon](https://docs.telethon.dev/)
- Inspired by the need for systematic Telegram content organization
- Thanks to all contributors

---

📮 For questions or issues, please open a GitHub issue.

Would you like me to add or modify any sections?
