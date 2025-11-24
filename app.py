from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import threading
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging

app = Flask(__name__)
CORS(app)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
# Global variables
bot_thread = None
bot_running = False
bot_paused = False
driver = None

def safe_wait_and_click(driver, wait, selectors, description, timeout=15):
    """Try multiple selectors and click the first one that works"""
    print(f"🔍 Looking for {description}...")
    for selector_type, selector in selectors:
        try:
            if selector_type == "xpath":
                element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            elif selector_type == "css":
                element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            
            element.click()
            print(f"✅ Clicked {description}")
            return True
        except Exception as e:
            print(f"⚠️ Selector failed: {selector[:50]}...")
            continue
    
    print(f"❌ Could not find {description}")
    return False

def extract_channel_info(driver, wait):
    channels = []
    usernames = []    
    try:
        print("⏳ Waiting for page to fully load...")
        time.sleep(8)  # Increased wait time
        
        # Scroll to load more channels
        print("📜 Scrolling to load channels...")
        for i in range(3):
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)
        
        try:
            # Multiple possible selectors for channel links
            selectors = [
                "a[href*='/'][data-a-target='preview-card-image-link']",
                "a[data-a-target='preview-card-image-link']",
                "a.preview-card-image-link",
                "a[href^='/']"
            ]
            
            links = []
            for selector in selectors:
                try:
                    links = driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(links) > 0:
                        print(f"✅ Found {len(links)} channel links using selector: {selector}")
                        break
                except:
                    continue
            
            if not links:
                print("❌ No channel links found with any selector")
                return []
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and 'twitch.tv/' in href:
                        username = href.rstrip('/').split('/')[-1].split('?')[0]
                        if username and username not in usernames and len(username) > 0 and username != 'directory':
                            usernames.append(username)
                            print(f"   📝 Found channel: {username}")
                except:
                    continue
        except Exception as e:
            print(f"❌ Error finding links: {e}")
            return []                
        
        # Take first 5 unique channels
        for username in usernames[:5]:
            channel_info = {
                'name': username,
                'url': f"https://www.twitch.tv/{username}"
            }
            channels.append(channel_info)
            print(f"✅ Added to list: {username}")
        
        print(f"\n🎯 Total channels found: {len(channels)}")
        return channels        
    except Exception as e:
        print(f"❌ Error extracting channels: {e}")
        import traceback
        traceback.print_exc()
        return []

def send_message_in_chat(driver, wait, channel_name, message):
    print(f"\n🔄 Visiting channel: {channel_name}")    
    try:
        driver.get(f"https://www.twitch.tv/{channel_name}")
        print("⏳ Waiting for page to load...")
        time.sleep(8)  # Increased wait
        
        # Close any popups
        try:
            close_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Close']")
            for btn in close_buttons:
                try:
                    btn.click()
                    time.sleep(1)
                except:
                    pass
        except:
            pass
        
        print("🔍 Looking for chat input box...")
        try:
            # Multiple selectors for chat input
            chat_selectors = [
                ("xpath", "//div[@role='textbox' and @data-a-target='chat-input']"),
                ("xpath", "//div[@data-a-target='chat-input']"),
                ("css", "div[data-a-target='chat-input']"),
                ("css", "textarea[data-a-target='chat-input']"),
            ]
            
            chat_input = None
            for selector_type, selector in chat_selectors:
                try:
                    if selector_type == "xpath":
                        chat_input = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    else:
                        chat_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    
                    if chat_input:
                        print(f"✅ Found chat input with {selector_type}")
                        break
                except:
                    continue
            
            if not chat_input:
                print("❌ Could not find chat input")
                return False
            
            # Try to click and focus
            try:
                chat_input.click()
            except:
                driver.execute_script("arguments[0].click();", chat_input)
            
            time.sleep(2)
            
            # Send message
            chat_input.send_keys(message)
            time.sleep(1)
            chat_input.send_keys(Keys.RETURN)
            
            print(f"✅ Sent '{message}' in {channel_name}'s chat!")
            time.sleep(3)
            return True            
        except TimeoutException:
            print("⚠️ Chat might be disabled, in subscriber-only mode, or you need to verify your account")
            return False
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False            
    except Exception as e:
        print(f"❌ Error visiting {channel_name}: {e}")
        return False

def run_bot(message):
    global bot_running, bot_paused, driver
    options = uc.ChromeOptions()
    
    print("=" * 60)
    print("🚀 BOT STARTED")
    print("=" * 60)
    
    try:
        print("\n[1/7] Creating Chrome driver...")
        driver = uc.Chrome(options=options, headless=False, use_subprocess=False, version_main=None)
        print("✅ Chrome driver created!")
        
        print("\n[2/7] Opening Twitch.tv...")
        driver.get("https://www.twitch.tv/")
        driver.maximize_window()
        print("✅ Twitch opened!")
        time.sleep(5)
        
        wait = WebDriverWait(driver, 20)
        
        print("\n[3/7] Attempting to search for Fortnite...")
        
        # Method 1: Try search box
        search_success = False
        try:
            search_selectors = [
                ("xpath", '//input[@placeholder="Search"]'),
                ("xpath", '//input[@type="search"]'),
                ("css", 'input[placeholder="Search"]'),
                ("css", 'input[type="search"]'),
                ("css", 'input[aria-label="Search"]'),
            ]
            
            for selector_type, selector in search_selectors:
                try:
                    if selector_type == "xpath":
                        search_input = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    else:
                        search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    
                    print(f"✅ Found search box with {selector_type}")
                    search_input.clear()
                    search_input.send_keys("Fortnite")
                    time.sleep(2)
                    search_input.send_keys(Keys.RETURN)
                    time.sleep(5)
                    search_success = True
                    break
                except:
                    continue
        except:
            pass
        
        # Method 2: Navigate directly if search fails
        if not search_success:
            print("⚠️ Search box not found, navigating directly...")
            driver.get("https://www.twitch.tv/directory/category/fortnite")
            time.sleep(8)
        
        print("\n[4/7] Ensuring we're on Fortnite category page...")
        
        # Make sure we're on the category page
        if "category/fortnite" not in driver.current_url.lower():
            print("📍 Not on category page, navigating directly...")
            driver.get("https://www.twitch.tv/directory/category/fortnite")
            time.sleep(8)
        
        print("✅ On Fortnite category page!")
        
        print("\n[5/7] Applying viewer count filter (ascending)...")
        # Navigate directly to sorted URL
        driver.get("https://www.twitch.tv/directory/category/fortnite?sort=VIEWER_COUNT_ASC")
        time.sleep(10)
        print("✅ Filter applied!")
        
        print("\n[6/7] Extracting channel information...")
        print("⏸️ PAUSED - Waiting for user to press Resume...")
        bot_paused = True
        while bot_paused and bot_running:
            time.sleep(0.5)
        
        if not bot_running:
            print("🛑 Bot stopped by user during pause")
            return
        
        print("▶️ RESUMED!")
        
        channels = extract_channel_info(driver, wait)
        
        if not channels:
            print("❌ No channels found! The page might not have loaded correctly.")
            return
        
        print(f"\n[7/7] Sending messages to {len(channels)} channels...")
        print(f"📝 Message to send: '{message}'")
        print("-" * 60)
        
        for i, channel in enumerate(channels):
            if not bot_running:
                print("🛑 Bot stopped by user")
                break
            
            print(f"\n[Channel {i+1}/{len(channels)}]")
            success = send_message_in_chat(driver, wait, channel['name'], message)
            
            if success:
                print(f"✅ Success!")
            else:
                print(f"⚠️ Failed or skipped")
            
            if i < len(channels) - 1:
                print("⏳ Waiting 5 seconds before next channel...")
                time.sleep(5)
        
        print("\n" + "=" * 60)
        print("✅ BOT COMPLETED ALL TASKS!")
        print("=" * 60)
        time.sleep(5)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ CRITICAL ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            try:
                print("\n🔒 Closing browser...")
                driver.quit()
                print("✅ Browser closed")
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")
        bot_running = False
        bot_paused = False
        print("🏁 Bot thread ended\n")

@app.route('/')
def index():
    return render_template('front.html')

@app.route('/start_bot', methods=['POST'])
def start_bot():
    global bot_thread, bot_running, bot_paused
    
    data = request.json
    message = data.get('message', '')
    
    print(f"\n📥 Received start_bot request")
    print(f"📝 Message: '{message}'")
    
    if not message:
        print("❌ No message provided")
        return jsonify({'status': 'error', 'message': 'No message provided'}), 400
    
    if bot_running:
        print("❌ Bot is already running")
        return jsonify({'status': 'error', 'message': 'Bot is already running'}), 400
    
    bot_running = True
    bot_paused = False
    print("✅ Starting bot thread...")
    bot_thread = threading.Thread(target=run_bot, args=(message,), daemon=True)
    bot_thread.start()
    print("✅ Bot thread started\n")
    
    return jsonify({'status': 'success', 'message': 'Bot started successfully'})

@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    global bot_running, bot_paused, driver
    
    print("\n🛑 Received stop_bot request")
    bot_running = False
    bot_paused = False
    
    if driver:
        try:
            driver.quit()
            print("✅ Driver quit successfully")
        except Exception as e:
            print(f"⚠️ Error quitting driver: {e}")
    
    return jsonify({'status': 'success', 'message': 'Bot stopped successfully'})

@app.route('/resume_bot', methods=['POST'])
def resume_bot():
    global bot_paused
    
    print("\n▶️ Received resume_bot request")
    
    if not bot_paused:
        return jsonify({'status': 'error', 'message': 'Bot is not paused'}), 400
    
    bot_paused = False
    print("✅ Bot resumed\n")
    
    return jsonify({'status': 'success', 'message': 'Bot resumed successfully'})

@app.route('/bot_status', methods=['GET'])
def bot_status():
    return jsonify({
        'running': bot_running,
        'paused': bot_paused
    })

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 TWITCH BOT SERVER STARTING")
    print("=" * 60)
    print("📡 Server URL: http://localhost:5000")
    print("💡 Open this URL in your browser to control the bot")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000, use_reloader=False)