from telethon import TelegramClient, types
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import asyncio
import re
from pathlib import Path
try:
    from config import CHANNELS  # private config
except ImportError:
    CHANNELS = ['@example_channel']  # default for public


# Load credentials
load_dotenv()
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')

async def get_channel_messages(client, channel, days=None, hours=24):
    messages = []
    
    if days is not None:
        time_delta = timedelta(days=days)
    else:
        time_delta = timedelta(hours=hours)
    
    since_date = datetime.now() - time_delta
    
    async for message in client.iter_messages(
        channel,
        offset_date=since_date,
        reverse=True
    ):
        # Download media if present
        media_path = await download_message_media(message, channel) if message.media else None
        
        msg_data = {
            'date': message.date.strftime('%Y-%m-%d %H:%M'),
            'text': message.text if message.text else '',
            'channel': channel,
            'has_media': bool(message.media),
            'media_path': media_path,
            'message_link': f"https://t.me/{channel}/{message.id}" if hasattr(channel, 'username') else None,
            'views': getattr(message, 'views', 0),
            'forwards': getattr(message, 'forwards', 0),
            'entities': []
        }
        
        if message.entities:
            for entity in message.entities:
                if hasattr(entity, 'url'):
                    msg_data['entities'].append({
                        'type': 'url',
                        'url': entity.url
                    })
                elif isinstance(entity, types.MessageEntityTextUrl):
                    msg_data['entities'].append({
                        'type': 'text_url',
                        'url': entity.url
                    })
                elif isinstance(entity, types.MessageEntityMention):
                    msg_data['entities'].append({
                        'type': 'mention',
                        'text': message.text[entity.offset:entity.offset+entity.length]
                    })
        
        messages.append(msg_data)
    
    return messages

async def save_messages_to_markdown(messages, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        # Document title
        f.write(f"# Telegram Channel Messages\n")
        f.write(f"_Collected on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n")
        
        # Group messages by channel
        channel_messages = {}
        for msg in messages:
            channel = msg['channel']
            if channel not in channel_messages:
                channel_messages[channel] = []
            channel_messages[channel].append(msg)
        
        # Write messages for each channel
        for channel, msgs in channel_messages.items():
            f.write(f"## Channel: {channel}\n\n")
            
            for msg in msgs:
                # Message header with date
                f.write(f"### {msg['date']}\n\n")
                
                # Message stats
                f.write(f"_Views: {msg['views']} | Forwards: {msg['forwards']}_\n\n")
                
                # Main message text
                if msg['text']:
                    text = msg['text']
                    text = re.sub(r'(?<!\\)\[(?!.*?\]\(.*?\))', r'\[', text)
                    text = re.sub(r'(?<!\\)\](?!.*?\))', r'\]', text)
                    f.write(f"{text}\n\n")
                
                # Media attachment
                if msg['has_media'] and msg['media_path']:
                    if msg['media_path'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        f.write(f"![Media]({msg['media_path']})\n\n")
                    else:
                        f.write(f"[📎 Attached Media]({msg['media_path']})\n\n")
                
                # Links and mentions
                if msg['entities']:
                    f.write("**Links and mentions:**\n\n")
                    for entity in msg['entities']:
                        if entity['type'] in ['url', 'text_url']:
                            f.write(f"🔗 [{entity['url']}]({entity['url']})\n")
                        elif entity['type'] == 'mention':
                            f.write(f"@ {entity['text']}\n")
                    f.write("\n")
                
                # Original message link
                if msg['message_link']:
                    f.write(f"🔗 [Original message]({msg['message_link']})\n\n")
                
                # Separator between messages
                f.write("---\n\n")
                
async def download_message_media(message, channel_name, media_dir="telegram_media"):
    """Download media from a message and return the local path"""
    if not message.media:
        return None
        
    # Create channel-specific directory
    channel_dir = Path(media_dir) / channel_name
    channel_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Generate filename with timestamp and message ID
        timestamp = message.date.strftime('%Y%m%d_%H%M%S')
        base_filename = f"{timestamp}_{message.id}"
        
        # Download the media
        downloaded_path = await message.download_media(
            file=channel_dir / base_filename
        )
        
        if downloaded_path:
            return str(Path(downloaded_path).relative_to(Path.cwd()))
        return None
        
    except Exception as e:
        print(f"Error downloading media: {e}")
        return None
    
async def main():
    client = TelegramClient('newsletter_session', API_ID, API_HASH)
    await client.start()

    channels = CHANNELS
    
    all_messages = []
    
    # Fetch messages from each channel
    for channel_username in channels:
        try:
            print(f"Fetching messages from {channel_username}...")
            # You can modify these parameters as needed:
            # Default (last 24 hours): await get_channel_messages(client, channel_username)
            # Specific days: await get_channel_messages(client, channel_username, days=3)
            # Specific hours: await get_channel_messages(client, channel_username, hours=12)
            messages = await get_channel_messages(client, channel_username, days=2)
            all_messages.extend(messages)
            print(f"Found {len(messages)} messages in {channel_username}")
        except Exception as e:
            print(f"Error fetching from {channel_username}: {e}")
    
    all_messages.sort(key=lambda x: x['date'])
    
    # Generate filename with current date
    filename = f"telegram_messages_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    await save_messages_to_markdown(all_messages, filename)
    print(f"\nMessages saved to {filename}")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())