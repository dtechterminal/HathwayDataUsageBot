📡 Hathway TG Bot

A Telegram bot that allows users to request and authenticate via OTP, then fetches and displays broadband data usage and account details from Hathway’s ISP portal.

⸻

✨ Features
	•	Request OTP using a mobile number
	•	Validate OTP and authenticate with Hathway’s API
	•	Automatically saves session information
	•	Fetches and displays broadband usage, plan, speed, service status, and payment details
	•	Uses Markdown formatting to present clean Telegram replies

⸻

🛠 Requirements
	•	Python 3.8+
	•	A Telegram bot token (get it via BotFather)
	•	Hathway ISP credentials (mobile number, account number)

⸻

📦 Installation
1.	Clone the repository:

		git clone https://github.com/dtechterminal/HathwayDataUsageBot.git
		cd hathway-tg-bot

2.	Install dependencies:

		pip install -r requirements.txt
		
		If requirements.txt is missing, install manually:
		
		pip install python-telegram-bot requests

3.	Create the following files:

		•	decoder.py: Include the functions decrypt_string() and encrypt_string() used for encrypting/decrypting user data (you must define these securely based on your app’s logic).
		•	session.json: A file to persist the session state. It will be created automatically on login.

4.	Set your Telegram Bot Token:

		Open bot.py and replace this line in the main() function:
		
		bot_token = ""  # Replace with your token
		
		With your actual token:
		
		bot_token = "YOUR_TELEGRAM_BOT_TOKEN"


⸻

🚀 Running the Bot

Once everything is set up:

	python bot.py

You should see:

	🤖 Bot is running...

Now send /start in Telegram to your bot and follow the prompts.

⸻

🤖 Bot Commands & Usage
	•	/start: Starts the bot
	•	Send a 10-digit mobile number to receive an OTP
	•	Enter the 6-digit OTP you receive
	•	Type hi or remaining data to fetch usage and plan details

⸻

📋 Notes
	•	The bot uses hardcoded API endpoints from Hathway’s mobile API.
	•	The bot stores session data locally in session.json for continuity.
	•	Retry logic and error handling are built in for robustness.

⸻

🔐 Disclaimer

This bot interacts with the Hathway private API endpoints and is intended for educational/personal use only. Use responsibly and at your own risk.
