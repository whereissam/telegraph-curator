from telethon import TelegramClient, types
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import asyncio
import re
from pathlib import Path
try:
    from config import GROUPS  # private config
except ImportError:
    GROUPS = ['@example_group']  # default for public

# Load credentials
load_dotenv()
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')

async def download_message_media(message, group_name, media_dir="telegram_group_media"):
    """Download media from a message and return the local path"""
    if not message.media:
        return None
        
    # Create group-specific directory
    group_dir = Path(media_dir) / group_name
    group_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Generate filename with timestamp and message ID
        timestamp = message.date.strftime('%Y%m%d_%H%M%S')
        base_filename = f"{timestamp}_{message.id}"
        
        # Download the media
        downloaded_path = await message.download_media(
            file=group_dir / base_filename
        )
        
        if downloaded_path:
            return str(Path(downloaded_path).relative_to(Path.cwd()))
        return None
        
    except Exception as e:
        print(f"Error downloading media: {e}")
        return None

async def get_group_messages(client, group, days=None, hours=24):
    """Fetch all messages from all participants in a group"""
    messages = []
    
    if days is not None:
        time_delta = timedelta(days=days)
    else:
        time_delta = timedelta(hours=hours)
    
    since_date = datetime.now() - time_delta
    
    async for message in client.iter_messages(
        group,
        offset_date=since_date,
        reverse=True
    ):
        # Get sender information properly
        sender = await message.get_sender()
        
        # Handle different types of senders
        if hasattr(sender, 'first_name'):  # User
            sender_info = {
                'id': sender.id,
                'type': 'user',
                'first_name': sender.first_name,
                'last_name': getattr(sender, 'last_name', ''),
                'username': getattr(sender, 'username', None)
            }
        elif hasattr(sender, 'title'):  # Channel or Anonymous Admin
            sender_info = {
                'id': sender.id,
                'type': 'channel',
                'title': sender.title,
                'username': getattr(sender, 'username', None)
            }
        else:
            sender_info = {
                'type': 'unknown',
                'name': 'Unknown Sender'
            }
        
        # Get reply information
        reply_to = None
        if message.reply_to:
            try:
                replied_msg = await message.get_reply_message()
                if replied_msg:
                    replied_sender = await replied_msg.get_sender()
                    reply_to = {
                        'message_id': replied_msg.id,
                        'text': replied_msg.text[:100] + '...' if replied_msg.text and len(replied_msg.text) > 100 else replied_msg.text,
                        'sender_id': replied_sender.id if replied_sender else None,
                        'sender_name': getattr(replied_sender, 'first_name', getattr(replied_sender, 'title', 'Unknown'))
                    }
            except Exception as e:
                print(f"Error getting reply message: {e}")

        # Create comprehensive message data
        msg_data = {
            'id': message.id,
            'date': message.date.strftime('%Y-%m-%d %H:%M'),
            'sender': sender_info,
            'text': message.text if message.text else '',
            'reply_to': reply_to,
            'forward_from': {
                'name': message.forward.sender.first_name if message.forward and hasattr(message.forward.sender, 'first_name') else None,
                'channel': message.forward.channel.title if message.forward and hasattr(message.forward, 'channel') else None
            } if message.forward else None,
            'has_media': bool(message.media),
            'message_link': f"https://t.me/c/{str(message.chat_id)[4:]}/{message.id}" if message.chat_id else None,
            'views': getattr(message, 'views', 0),
            'reactions': getattr(message, 'reactions', None),
            'entities': []
        }
        
        # Process message entities (mentions, URLs, etc.)
        if message.entities:
            for entity in message.entities:
                entity_data = None
                
                if hasattr(entity, 'url'):
                    entity_data = {'type': 'url', 'url': entity.url}
                elif isinstance(entity, types.MessageEntityTextUrl):
                    entity_data = {'type': 'text_url', 'url': entity.url}
                elif isinstance(entity, types.MessageEntityMention):
                    entity_data = {
                        'type': 'mention',
                        'text': message.text[entity.offset:entity.offset+entity.length]
                    }
                
                if entity_data:
                    msg_data['entities'].append(entity_data)
        
        messages.append(msg_data)
    
    return messages

async def save_group_messages_to_markdown(messages, filename):
    """Save group messages in Markdown format"""
    with open(filename, 'w', encoding='utf-8') as f:
        # Document title
        f.write(f"# Telegram Group Messages\n")
        f.write(f"_Collected on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n")
        
        for msg in messages:
            # Message header with date and sender - handle different sender types
            f.write(f"### {msg['date']} - ")
            
            sender = msg['sender']
            if sender['type'] == 'user':
                # For users, show first name and username if available
                f.write(f"{sender['first_name']}")
                if sender.get('username'):
                    f.write(f" (@{sender['username']})")
            elif sender['type'] == 'channel':
                # For channels, show title and username if available
                f.write(f"{sender['title']}")
                if sender.get('username'):
                    f.write(f" (@{sender['username']})")
            else:
                # For unknown senders
                f.write("Unknown Sender")
            
            f.write("\n\n")
            
            # Reply information
            if msg['reply_to']:
                f.write(f"> Replying to: {msg['reply_to']['text']}\n\n")
            
            # Main message text
            if msg['text']:
                text = msg['text']
                text = re.sub(r'(?<!\\)\[(?!.*?\]\(.*?\))', r'\[', text)
                text = re.sub(r'(?<!\\)\](?!.*?\))', r'\]', text)
                f.write(f"{text}\n\n")
            
            # Media attachment
            if msg['has_media'] and msg.get('media_path'):
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
            
            # Message link
            if msg['message_link']:
                f.write(f"🔗 [Original message]({msg['message_link']})\n\n")
            
            # Separator between messages
            f.write("---\n\n")
            
async def main():
    client = TelegramClient('group_reader_session', API_ID, API_HASH)
    await client.start()
    
    groups = GROUPS
    
    all_messages = []
    
    for group_identifier in groups:
        try:
            print(f"Fetching messages from {group_identifier}...")
            messages = await get_group_messages(client, group_identifier)
            all_messages.extend(messages)
            print(f"Found {len(messages)} messages in {group_identifier}")
        except Exception as e:
            print(f"Error fetching from {group_identifier}: {e}")
    
    all_messages.sort(key=lambda x: x['date'])
    
    filename = f"telegram_group_messages_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    await save_group_messages_to_markdown(all_messages, filename)
    print(f"\nMessages saved to {filename}")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())