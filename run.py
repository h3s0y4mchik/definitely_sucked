import asyncio
import customtkinter as ctk
from pyrogram import Client, filters
from pyrogram.types import Message
import json
import os
import threading
import sys

# Global variables
TARGET_USERS = []
FILTERS = []
api_id = ""
api_hash = ""
bot_running = False
bot_app = None

# Path to settings file
SETTINGS_FILE = "settings.json"

# Load settings
def load_settings():
    global TARGET_USERS, FILTERS, api_id, api_hash
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                TARGET_USERS = settings.get("users", [])
                FILTERS = settings.get("filters", [])
                api_id = settings.get("api_id", "")
                api_hash = settings.get("api_hash", "")
            log_message("Settings loaded successfully.")
        except Exception as e:
            log_message(f"Error loading settings: {str(e)}", "error")

# Save settings
def save_settings():
    settings = {
        "users": TARGET_USERS,
        "filters": FILTERS,
        "api_id": api_id,
        "api_hash": api_hash
    }
    try:
        with open(SETTINGS_FILE, "w", encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        log_message("Settings saved successfully.")
    except Exception as e:
        log_message(f"Error saving settings: {str(e)}", "error")

# Log messages
def log_message(message, level="info"):
    if not gui_mode:  # If not in GUI mode, print directly to the console
        print(f"[{level.upper()}] {message}")
    else:
        log_box.insert("end", f"[{level.upper()}] {message}\n")
        log_box.yview("end")  # Scroll to the end

# Asynchronous bot start
async def start_bot(api_id, api_hash):
    await process_input()
    global bot_running, bot_app
    bot_running = True
    bot_app = Client("my_account", api_id=api_id, api_hash=api_hash)

    @bot_app.on_message(filters.private & filters.incoming)
    async def react_to_message(client: Client, message: Message):
        username = message.from_user.username
        if message.from_user.id in TARGET_USERS or username in TARGET_USERS or f'@{username}' in TARGET_USERS:
            try:
                if message.text:
                    message_lower = message.text.lower()
                    if any(filter_text.lower() in message_lower for filter_text in FILTERS):
                        if message.reply_to_message and message.reply_to_message.from_user.id == bot_app.me.id:
                            # Если это ответ на сообщение и оно принадлежит боту
                            await message.reply_to_message.edit("Сосал?")
                            log_message(f"Edited replied message for {message.from_user.username or message.from_user.id}")
                        else:
                            # Если это обычное сообщение, редактируем предыдущее
                            async for prev_message in bot_app.get_chat_history(message.chat.id, limit=2):
                                if prev_message.id != message.id and prev_message.from_user.id == bot_app.me.id:
                                    await prev_message.edit("Сосал?")
                                    log_message(f"Edited previous message from {message.from_user.username or message.from_user.id}")
                                    break
            except Exception as e:
                log_message(f"Error while processing message: {str(e)}", "error")

    await bot_app.start()
    log_message(f"Bot started.")

# Asynchronous bot stop
async def stop_bot():
    global bot_running, bot_app
    if bot_running:
        await bot_app.stop()
        bot_running = False
        log_message("Bot stopped.")

# Toggle bot start/stop
def toggle_bot():
    global bot_running
    if bot_running:
        log_message("Stopping bot...")
        loop.call_soon_threadsafe(lambda: asyncio.create_task(stop_bot()))
        start_button.configure(text="Start Bot")
    else:
        log_message("Starting bot...")
        start_button.configure(text="Stop Bot")
        loop.call_soon_threadsafe(lambda: asyncio.create_task(start_bot(api_id, api_hash)))

# Handle input and start the bot
async def process_input():
    global TARGET_USERS, FILTERS, api_id, api_hash
    
    user_input = []
    filters_input = []
    api_id_input = ""
    api_hash_input = ""
    
    if not TARGET_USERS or not FILTERS or not api_id or not api_hash:
        # Get values from the input fields or console
        user_input = user_ids_input.get().strip().split() if gui_mode else input("Enter user IDs or usernames (separate by space): ").strip().split()
        filters_input = filters_list_input.get().strip().split() if gui_mode else input("Enter filters (separate by space): ").strip().split()

        # Check for API keys
        api_id = api_id_input.get().strip() if gui_mode else input("Enter API ID: ").strip()
        api_hash = api_hash_input.get().strip() if gui_mode else input("Enter API Hash: ").strip()

        if not api_id or not api_hash:
            log_message("API ID and API Hash are required!", "error")
            return
    else:
        user_input = TARGET_USERS
        filters_input = FILTERS
        api_id_input = api_id
        api_hash_input = api_hash
    
    # Process user input
    TARGET_USERS = []
    for item in user_input:
        if item.isdigit():
            TARGET_USERS.append(int(item))
        else:
            TARGET_USERS.append(item)

    # Save filters
    FILTERS = filters_input

    log_message(f"Users: {TARGET_USERS}")
    log_message(f"Filters: {FILTERS}")

    # Save settings
    save_settings()

# Start asyncio loop in a separate thread
def start_async_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Exit the application
def exit_application():
    root.quit()
    loop.stop()

# Set up customtkinter (only in GUI mode)
def setup_gui():
    global gui_mode
    gui_mode = True
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    global root, api_id_input, api_hash_input, user_ids_input, filters_list_input, start_button, exit_button, log_box
    root = ctk.CTk()
    root.title("Bot Setup")

    # API ID input
    api_id_label = ctk.CTkLabel(root, text="Enter API ID:")
    api_id_label.pack(pady=10)
    api_id_input = ctk.CTkEntry(root, width=300)
    api_id_input.pack(pady=10)

    # API Hash input
    api_hash_label = ctk.CTkLabel(root, text="Enter API Hash:")
    api_hash_label.pack(pady=10)
    api_hash_input = ctk.CTkEntry(root, width=300)
    api_hash_input.pack(pady=10)

    # User input
    user_label = ctk.CTkLabel(root, text="Enter usernames or user_ids (separate by space):")
    user_label.pack(pady=10)
    user_ids_input = ctk.CTkEntry(root, width=300)
    user_ids_input.pack(pady=10)

    # Filters input
    filters_label = ctk.CTkLabel(root, text="Enter filters (separate by space):")
    filters_label.pack(pady=10)
    filters_list_input = ctk.CTkEntry(root, width=300)
    filters_list_input.pack(pady=10)

    # Start/Stop button
    start_button = ctk.CTkButton(root, text="Start Bot", command=toggle_bot)
    start_button.pack(pady=20)

    # Exit button
    exit_button = ctk.CTkButton(root, text="Exit", command=exit_application)
    exit_button.pack(pady=10)

    # Log box
    log_label = ctk.CTkLabel(root, text="Log:")
    log_label.pack(pady=10)
    log_box = ctk.CTkTextbox(root, width=300, height=150)
    log_box.pack(pady=10)

    # Load settings at startup
    load_settings()

    # Pre-fill the input fields
    if api_id:
        api_id_input.insert(0, api_id)
    if api_hash:
        api_hash_input.insert(0, api_hash)
    if TARGET_USERS:
        user_ids_input.insert(0, " ".join(map(str, TARGET_USERS)))
    if FILTERS:
        filters_list_input.insert(0, " ".join(FILTERS))

    # Start the asyncio event loop in a separate thread
    threading.Thread(target=start_async_loop, daemon=True).start()
    root.mainloop()

def setup_cli():
    global gui_mode
    gui_mode = False  # Mark that we are in CLI mode
    load_settings()  # Try loading settings
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    if not TARGET_USERS or not FILTERS or not api_id or not api_hash:
        log_message("Starting without GUI. You must input necessary details.")
        loop.run_until_complete(process_input())  # Process input via console
    
    try:
        loop.run_until_complete(start_bot(api_id, api_hash))
        # Start the asyncio event loop
        loop.run_forever()
    except KeyboardInterrupt:
        # Stop the asyncio event loop on keyboard interrupt
        log_message("Stopping bot...", "info")
        loop.run_until_complete(stop_bot())
        loop.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--no-gui":
        setup_cli()
    else:
        setup_gui()
