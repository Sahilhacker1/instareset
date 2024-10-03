import telebot
import requests
import logging
import instaloader
from uuid import uuid4 as uid

# Configuration
BOT_TOKEN = "7710011490:AAH2UuklvraWuyHGE5wwbc0dZ9IQmSdUadg"
CSRF_TOKEN = "BbJnjd.Jnw20VyXU0qSsHLV"
CHANNEL_ID = -1002497737475  # Replace with your channel ID

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

async def log_new_user(user):
    user_details = f"""
    New user for RESET
    Name: {user.full_name}
    ID: {user.id}
    """
    # Send user details to the channel
    await bot.send_message(chat_id=CHANNEL_ID, text=user_details)

    # Send user profile picture to the channel
    profile_pics = await bot.get_user_profile_photos(user.id)
    if profile_pics.photos:
        profile_pic_file_id = profile_pics.photos[0][0].file_id
        await bot.send_photo(chat_id=CHANNEL_ID, photo=profile_pic_file_id)
    else:
        await bot.send_message(chat_id=CHANNEL_ID, text="User has no profile picture.")

@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    user_id = user.id
    user_name = user.full_name

    # Log new user
    log_new_user(user)

    # Welcome message
    bot.send_message(
        message.chat.id,
        f"<b>Heyy Buddy!\nWelcome::\nPlease Support Our Small Community=@join_hyponet ~HypoNet\nBuddy=⭕️{user_name}!</b>\nYour User ID: <code>{user_id}❗️</code>",
        parse_mode='HTML'
    )

    show_options(message.chat.id)

def show_options(chat_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton("RESET-USERNAME⚡️", callback_data='username'),
        telebot.types.InlineKeyboardButton("RESET-Email 📲 ", callback_data='email'),
        telebot.types.InlineKeyboardButton("Get Instagram Details 🎭 ", callback_data='instagram')
    )
    bot.send_message(chat_id, "Welcome!\n ⚡️ Please choose an option:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def button_handler(call):
    option = call.data
    bot.send_message(call.message.chat.id, f"Please send me your {option}.")
    bot.register_next_step_handler(call.message, receive_input, option)

def receive_input(message, input_type):
    user_input = message.text

    if input_type == 'instagram':
        bot.send_message(message.chat.id, "Please provide a proxy (format: http://username:password@ip:port) for Instagram requests.")
        bot.register_next_step_handler(message, handle_instagram_request, user_input)
    elif input_type in ['username', 'email']:
        handle_account_recovery(message, user_input, input_type)

def handle_account_recovery(message, user_input, input_type):
    url = "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/"
    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded",
        "cookie": f"csrftoken={CSRF_TOKEN}",
        "origin": "https://www.instagram.com",
        "referer": "https://www.instagram.com/accounts/password/reset/?source=fxcal",
        "user-agent": "Mozilla/5.0",
        "x-asbd-id": "129477",
        "x-csrftoken": CSRF_TOKEN,
        "x-ig-app-id": "1217981644879628",
        "x-instagram-ajax": "1015181662",
        "x-requested-with": "XMLHttpRequest"
    }

    data = {
        "email_or_username": user_input,
        "flow": "fxcal"
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        bot.send_message(message.chat.id, 'Success! Check your email for recovery instructions.')
    except requests.HTTPError as e:
        if e.response.status_code == 400:
            bot.send_message(message.chat.id, "The provided username or email does not exist. Please check and try again.")
        else:
            bot.send_message(message.chat.id, f'An unexpected error occurred: {e.response.text}. Please try again later.')
    except Exception as e:
        logger.error(f"An error occurred during account recovery: {str(e)}")
        bot.send_message(message.chat.id, 'An error occurred. Please try again later.')

def handle_instagram_request(message, username, proxy):
    # Set up a proxy
    session = requests.Session()
    if proxy:
        session.proxies = {
            'http': proxy,
            'https': proxy,
        }

    try:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Instagram 10.26.0 Android",
            "Cookie": f"csrftoken={CSRF_TOKEN}",
        }
        data = {
            "q": username,
            "device_id": f"android{uid()}",
            "guid": str(uid()),
            "_csrftoken": CSRF_TOKEN
        }
        response = session.post('https://i.instagram.com/api/v1/users/lookup/', headers=headers, data=data).json()

        if response.get('status') == 'fail':
            bot.send_message(message.chat.id, "Instagram user not found. Please try with another username.")
            return

        user_id = response.get('user', {}).get('pk', 'N/A')
        profile_info = ""

        try:
            L = instaloader.Instaloader()
            profile = instaloader.Profile.from_username(L.context, username)
            profile_info = (
                f"[+] Username: {profile.username}\n"
                f"[+] ID: {profile.userid}\n"
                f"[+] Full Name: {profile.full_name}\n"
                f"[+] Biography: {profile.biography}\n"
                f"[+] Followers: {profile.followers}\n"
                f"[+] Media Count: {profile.mediacount}\n"
                f"[+] Profile Picture URL: {profile.profile_pic_url}\n"
            )
        except Exception as e:
            logger.error(f"Error fetching profile info: {e}")
            profile_info = "Could not retrieve additional profile information."

        lookup_result = (
            f"[+] Username : {username}\n"
            f"[+] User ID : {user_id}\n"
            f"{profile_info}"
        )
        
        bot.send_message(message.chat.id, lookup_result)
        bot.send_message(message.chat.id,
                         "This bot provides only basic Instagram account details. For advanced details, "
                         "please use @MiniOsintBot. If you want to start again, use the /start command.")
    except Exception as e:
        logger.error(f'An error occurred while fetching Instagram details: {str(e)}')
        bot.send_message(message.chat.id, f'An error occurred while fetching Instagram details: {str(e)}')

# Start the bot
if __name__ == "__main__":
    print("Bot is polling...")
    bot.polling(none_stop=True)
    