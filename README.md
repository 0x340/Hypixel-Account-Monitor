# Hypixel SkyBlock Level Monitor

This small Python script polls the Hypixel API at a regular interval and notifies you when a monitored JSON value changes.

Features
- Poll any Hypixel endpoint (default `player`, also supports `skyblock/profiles`, `skyblock/profile`)
- Extract the monitored value using a JMESPath expression (flexible JSON querying)
- Console logging and optional Windows toast notifications (requires `win10toast`)
- Config via CLI or JSON config file

Files
- `monitor_hypixel.py` – the monitor script
- `config_sample.json` – example config
- `requirements.txt` – Python dependencies

Quick start
1. Install Python and create a virtualenv (optional).
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Get a Hypixel API key from: https://api.hypixel.net

4. Examples

Monitor a player's network level (player endpoint):

```powershell
python monitor_hypixel.py -k YOUR_API_KEY -u SomeUsername -e player -j "player.networkExp" -i 300 --notify
```

Monitor a SkyBlock profile field (you will need the player's UUID):
- Resolve UUID: `https://api.mojang.com/users/profiles/minecraft/<username>`
- Then call `skyblock/profiles` and use a JMESPath expression.

Example (monitor raw farming experience in first profile's member entry):

```powershell
python monitor_hypixel.py -k YOUR_API_KEY -e skyblock/profiles -j "profiles[0].members.'<uuid>'.experience_skill_farming" -i 300
```

Notes on JMESPath
- JMESPath is a powerful expression language for JSON. If you haven't used it before, see https://jmespath.org for examples.
- Use single quotes around UUID keys inside expressions as shown above.

Config file
Create a JSON config with these fields (optional):

```json
{
  "api_key": "YOUR_API_KEY",
  "username": "SomePlayer",
  "uuid": "playeruuidwithout-dashes",
  "endpoint": "skyblock/profiles",
  "jmespath": "profiles[0].members.'<uuid>'.experience_skill_farming",
  "interval": 300,
  "notify": true
}
```

Limitations and tips
- The script treats the first fetched value as the initial state and will print it but not send a "changed" notification for the initial fetch.
- Hypixel API rate limits apply; polling every 5 minutes is safe for most keys.
- If you want richer notifications (sound, actions), consider integrating other notification libraries.

