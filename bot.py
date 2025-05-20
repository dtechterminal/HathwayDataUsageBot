import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from decoder import decrypt_string, encrypt_string
from telegram.helpers import escape_markdown
from datetime import datetime

import logging
import json
import os
import time
import random

logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

API_URL = "https://ispselfcareadmin.hathway.net/api/isp/v2/customer/generateotp"

HEADERS = {
    "accept": "application/json",
    "Accept-Encoding": "gzip",
    "Connection": "Keep-Alive",
    "Content-Type": "application/json",
    "device_type": "1",
    "Host": "ispselfcareadmin.hathway.net",
    "User-Agent": "okhttp/4.9.2",
    "version": "4.2.17"
}

SESSION = {
    "token": None,
    "account_no": None,
    "mobile": None
}

SESSION_FILE = "session.json"

def load_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                SESSION.update(data)
        except Exception as e:
            logger.error(f"Failed to load session: {e}")

def save_session():
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(SESSION, f)
    except Exception as e:
        logger.error(f"Failed to save session: {e}")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # logger.error("Start command received.")
    await update.message.reply_text("Send me a mobile number to request an OTP.")

# Handle incoming mobile number
async def handle_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mobile = update.message.text.strip()
    # logger.error(f"Mobile received: {mobile}")

    if not mobile.isdigit() or len(mobile) != 10:
        await update.message.reply_text("❗ Please enter a valid 10-digit mobile number.")
        return

    payload = {
        "type": "registered_mobile_no",
        "input_value": mobile,
        "login_device": "mobile"
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        logger.error(f"OTP API response: {response.text}")
        data = response.json()

        if data.get("status") == "success":
            # Extract fields from the JSON
            message = data.get("responseMessage", "OTP Sent.")
            enc_mobile = decrypt_string(data.get("registered_mobile_no", ""))
            email = decrypt_string(data.get("email", ""))
            account_no = ", ".join(data.get("account_no", []))
            customer_name = decrypt_string(data.get("customer_name", ""))

            reply = (
                f"✅ *{message}*\n"
                f"\n*Encrypted Mobile:* `{enc_mobile}`"
                f"\n*Encrypted Email:* `{email}`"
                f"\n*Account No:* `{account_no}`"
                f"\n*Encrypted Name:* `{customer_name}`"
            )
            await update.message.reply_text(reply, parse_mode="Markdown")

            second_payload = {
                "registered_mobile_no": mobile,
                "email": email,
                "customer_name": customer_name
            }
            logger.error(f"Secondary OTP payload: {second_payload}")

            second_url = "https://ispselfcareadmin.hathway.net/api/isp/v1/customer/sendOtpOnPhoneNumber"
            second_response = requests.post(second_url, headers=HEADERS, json=second_payload)
            logger.error(f"Secondary OTP response: {second_response.text}")

            if second_response.status_code == 200:
                await update.message.reply_text("📲 Secondary OTP request sent successfully!")
                await update.message.reply_text("📩 Please enter the OTP you received:")
                context.chat_data["login_payload"] = {
                    "registered_mobile_no": data.get("registered_mobile_no", ""),
                    "account_no": data.get("account_no", [""])[0]
                }
                return
            else:
                await update.message.reply_text(f"⚠️ Secondary OTP request failed: {second_response.status_code}")

        else:
            await update.message.reply_text("❌ OTP request failed.")

    except Exception as e:
        logger.exception("Exception during handle_mobile:")
        await update.message.reply_text(f"⚠️ Error occurred: {str(e)}")

async def handle_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        otp = update.message.text.strip()
        login_info = context.chat_data.get("login_payload")
        if not login_info:
            await update.message.reply_text("❗ Please initiate the login process first by sending your mobile number.")
            return

        login_payload = {
            "registered_mobile_no": login_info["registered_mobile_no"],
            "otp": otp,
            "login_device": "mobile",
            "account_no": encrypt_string(login_info["account_no"])
        }
        logger.error(f"Login payload: {login_payload}")

        login_url = "https://ispselfcareadmin.hathway.net/api/isp/v2/customer/login"
        login_response = requests.post(login_url, headers=HEADERS, json=login_payload)
        logger.error(f"Login response: {login_response.text}")

        login_data = login_response.json()
        if login_response.status_code == 200 and login_data.get("status") == "success":
            token = login_data.get("token")

            await update.message.reply_text("🔓 Login successful! Token received.")

            SESSION["token"] = token
            SESSION["account_no"] = login_info["account_no"]
            SESSION["mobile"] = decrypt_string(login_info["registered_mobile_no"])
            save_session()

            # Save app version
            app_version_url = "https://ispselfcareadmin.hathway.net/api/isp/v1/version/saveAppVersion"
            app_version_headers = HEADERS.copy()
            app_version_headers["authorization"] = token

            version_payload = {
                "account_no": SESSION["account_no"],
                "registered_mobile_no": SESSION["mobile"],
                "device_type": 1,
                "login_device": "mobile",
                "app_version": "4.2.17"
            }
            logger.error(f"App version payload: {version_payload}")

            version_response = requests.post(app_version_url, headers=app_version_headers, json=version_payload)
            logger.error(f"App version response: {version_response.text}")
            if version_response.status_code == 200:
                await update.message.reply_text("📱 App version saved successfully.")
            else:
                await update.message.reply_text("⚠️ Failed to save app version.")
        else:
            await update.message.reply_text("❌ OTP validation failed. Please ensure you entered the correct code.")
    except Exception as e:
        logger.exception("Exception during handle_otp:")
        await update.message.reply_text("⚠️ An unexpected error occurred while processing your OTP.")

async def get_remaining_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # logger.error("Fetching remaining data...")
    if not SESSION["token"] or not SESSION["account_no"] or not SESSION["mobile"]:
        await update.message.reply_text("❗ You need to authenticate first by sending your mobile number.")
        return

    info_url = "https://ispselfcareadmin.hathway.net/api/isp/v2/customer/login"
    headers = HEADERS.copy()
    headers["authorization"] = SESSION["token"]

    payload = {
        "registered_mobile_no": SESSION["mobile"],
        "latitude": "",
        "longitude": "",
        "is_latlong": 1,
        "use": "info",
        "login_device": "mobile",
        "account_no": SESSION["account_no"]
    }
    logger.error(f"Info request payload: {payload}")

    max_retries = 5
    for attempt in range(1, max_retries + 1):
        await update.message.reply_text(f"🔄 Trying to fetch data... Attempt {attempt}")
        response = requests.post(info_url, headers=headers, json=payload)
        logger.error(f"Info API response: {response.text}")
        if response.status_code == 200 and response.json().get("status") == "success":
            result = response.json()
            customer = result.get("data", [{}])[0].get("customer", {})
            used = int(customer.get("data_usage_x", 0))
            total = int(customer.get("data_usage_y", 0))
            remaining_mb = round((total - used) / 1024, 2)
            total_mb = round(total / 1024, 2)
            first_name = escape_markdown(str(customer.get("first_name", "")), version=2)
            last_name = escape_markdown(str(customer.get("last_name", "")), version=2)
            mobile = escape_markdown(str(customer.get("registered_mobile_no", "")), version=2)
            email = escape_markdown(str(customer.get("email", "")), version=2)
            plan_name = escape_markdown(str(result["data"][0]["customer_plan"][0].get("plan_product_name", "")), version=2)
            # Plan speed formatting
            raw_speed = result["data"][0]["customer_plan"][0].get("plan_speed", "")
            if "/" in raw_speed:
                download_speed, upload_speed = map(str.strip, raw_speed.split("/"))
                formatted_speed = f"{download_speed} Download / {upload_speed} Upload"
            else:
                formatted_speed = raw_speed
            plan_speed = escape_markdown(formatted_speed, version=2)
            plan_end_days = escape_markdown(str(result["data"][0]["customer_plan"][0].get("no_of_days_left", "N/A")), version=2)
            city = escape_markdown(str(result["data"][0].get("city", "")), version=2)
            service_status = escape_markdown(str(result["data"][0]["customer_service"].get("service_status", "")), version=2)
            fup_status = escape_markdown(str(result["data"][0].get("fup_status", "")), version=2)
            account_no = escape_markdown(str(customer.get("account_no", "")), version=2)
            quota = escape_markdown(str(customer.get("quota", "")), version=2)
            last_payment_amount = escape_markdown(str(result["data"][0]["last_payment_details"].get("amount", "N/A")), version=2)
            # Last payment date formatting
            raw_date = result["data"][0]["last_payment_details"].get("last_payment_date")
            if raw_date:
                formatted_date = datetime.fromtimestamp(raw_date).strftime("%d-%m-%Y")
            else:
                formatted_date = "N/A"
            last_payment_date = escape_markdown(formatted_date, version=2)

            reply_message = (
                f"👤 *Name:* {first_name} {last_name}\n"
                f"📱 *Mobile:* {mobile}\n"
                f"📧 *Email:* {email}\n"
                f"🏙️ *City:* {city}\n"
                f"📦 *Plan:* {plan_name}\n"
                f"🚀 *Speed:* {plan_speed}\n"
                f"📅 *Days Left:* {plan_end_days}\n"
                f"📶 *Data:* {escape_markdown(str(remaining_mb), version=2)} GB remaining out of {escape_markdown(str(total_mb), version=2)} GB\n"
                f"🔌 *Service Status:* {service_status}\n"
                f"📊 *FUP Status:* {fup_status}\n"
                f"🆔 *Account No:* {account_no}\n"
                f"📡 *Quota:* {quota}\n"
                f"💳 *Last Payment:* ₹{last_payment_amount}\n"
                f"🕒 *Payment Date:* {last_payment_date}"
            )

            await update.message.reply_text(reply_message, parse_mode="MarkdownV2")
            break
        else:
            if attempt < max_retries:
                wait_time = random.randint(2, 5)
                time.sleep(wait_time)
            else:
                logger.error("Failed to fetch data usage info after retries.")
                await update.message.reply_text("⚠️ Could not fetch data usage info after multiple attempts.")

# Main bot entry point
def main():
    load_session()
    bot_token = ""  # Replace with your token

    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^(hi|remaining data)$"), get_remaining_data))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^\d{6}$"), handle_otp))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mobile))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()