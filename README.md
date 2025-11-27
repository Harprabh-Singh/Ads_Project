Twitch Automation Bot – README


This project is a Twitch Automation Bot built using Python, Selenium, undetected-chromedriver, and Flask, with a modern web UI made in HTML + Tailwind CSS.


The bot:
Opens Twitch automatically
Searches for Fortnite
Applies filters (viewers low → high)
Scrapes streamer channels
Opens streams
Sends automated chat messages
Supports pause, resume, stop
Fully controlled through a modern frontend


Run all of these commands:

pip install flask
pip install flask-cors
pip install undetected-chromedriver
pip install selenium


Project Structure
project-folder/
│
├── app.py
├── templates/
│     └── front.html
└── README.md


Flask will automatically load front.html from the templates folder.


How to Run the Bot

1. Open Terminal in the project folder
Then run:
python app.py

2. Open the control panel
Go to:
http://localhost:5000

3. Use the UI
Enter your message
Click Start Bot

The bot opens Chrome and starts working and on reaching filtered page it pauses and wait for you to log in
After logging in click Resume

Click Stop Bot anytime


Frontend (front.html)

The UI includes:
Twitch-themed gradients
Blurred animated blobs
Dark mode
Start Bot / Resume / Stop
Real-time bot status
Tailwind CSS styling
Modern glass-card layout
No external installation needed — only the HTML file.


Backend (app.py)

The backend:
Starts Flask REST API server
Controls Selenium driver
Sends chat messages
Scrapes channels

Handles:
/start_bot
/stop_bot
/resume_bot
/bot_status

The bot runs in a separate thread so the UI stays responsive.


Features

✔ Automation:
Opens Twitch
Navigates to Fortnite
Applies viewer sort filter
Scrolls to load channels
Extracts unique streamers
Sends chat automatically

✔ Safety Features:
Multi-selector detection
Try–Catch handling
Anti-popup closing
Anti-bot detection bypass

✔ Smart Execution:
Pauses before sending messages
Waits for user resume
Handles failures per channel


Technologies Used

Backend:
Python
Flask
Selenium
undetected-chromedriver
WebDriverWait
Threading

Frontend:
Tailwind CSS
HTML5
JavaScript
Fetch API

Common Fixes

Chrome version not matching?
Run: pip install undetected-chromedriver --upgrade

Browser does not open?
Install newest Chrome.

Selenium errors?
Reinstall: pip install selenium --upgrade


Conclusion

This project demonstrates real-world Twitch automation using Selenium combined with a clean Flask API and a polished frontend. The system is scalable, modern, and fully controllable without using the terminal.