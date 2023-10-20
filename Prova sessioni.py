from telethon import TelegramClient, utils

# Replace these with your own values
api_id = 'your_api_id'
api_hash = 'your_api_hash'
session_file = 'your_session_file'  # The name of the session file

async def main():
    # Get the username to send the message to
    username = input('Enter the username to send the message to: ')
    
    # Get the message to send
    message = input('Enter the message to send: ')
    
    # Search for the username and get the User object
    user = await client.get_input_entity(username)
    
    # Send the message
    await client.send_message(user, message)
    print(f'Message sent to {username}')

# Initialize the client and connect
client = TelegramClient(session_file, api_id, api_hash)

# Run the main function
with client:
    client.loop.run_until_complete(main())