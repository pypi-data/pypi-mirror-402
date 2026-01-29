# Hacking my Digital Hoarding, one file at a time

This is a personal project I whipped up to keep my fucking download folder organized for once. It is specifically tailored for my Mac setup and isn't intended for widespread distribution as a polished package. I'm sharing the code in a raw, custom way. If it helps you solve a similar problem or inspires your own automation tools, that's great!

## 🧠 The Problem: The Infinite Downloads Folder Syndrome

I tend to hoard files, installers, and documents with the false promise that *"they will be useful in the future."* Surprise: they never are. The result is a massive cognitive load that affects both my productivity and my Mac's storage.

This project is born from my own **"Mental Framework"** to hack digital hoarding:

1. **Identify the trash:** Recognizing single-use files (currently focusing on installers like `.dmg` or `.app`).
2. **Reduce detachment friction:** Instead of deleting them immediately (which triggers that *"what if I need it later?"* anxiety), I move them to a transition zone.
3. **Automate the habit:** I've realized that the cognitive cost and psychological resistance to deleting things are too high for me. I've accepted it. So, I prefer this script to act as my "organized self" and do the job for me automatically.

## 🚀 The Solution: Version 1.0

This is the first iteration of my cleaning assistant. It uses a **Watchdog** (filesystem observer) to monitor the downloads folder in real-time and apply my framework rules.

### How it works:

- **Auto-Detection:** The script watches for any new item arriving in the folder.
- **Smart Filter:** It specifically targets `.dmg` and `.app` extensions—the main culprits of unnecessary clutter.
- **Move, Don't Delete:** Files are moved to a `should-be-deleted` folder. This hacks the fear of loss, giving me a "grace period" before the final purge.
- **Duplicate Handling:** If I download the same installer multiple times, the script detects name collisions and assigns a random number to avoid errors and keep everything traceable.

## 🛠️ Technologies

- **Python 3.14+**
- [**uv**](https://github.com/astral-sh/uv): An extremely fast Python package installer and resolver.
- [**Watchdog**](https://python-watchdog.readthedocs.io/): A library to monitor filesystem events. It leverages native OS events to track folder changes in real-time, avoiding the overhead of constant polling.

## 📦 Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd download-cleaner
```

### 2. Install dependencies using `uv`

```bash
uv sync
```

### 3. Configuration

Open `main.py` and ensure the `downloads_folder` variable points to your directory:

```python
downloads_folder = Path("~/Downloads").expanduser()
```

## ⚙️ Run as a Service (macOS)

You can set this up as a background service using `launchd` so it runs automatically when you log in.

### 1. Create the Launch Agent

Create a file named `com.user.downloadcleaner.plist` in `~/Library/LaunchAgents/`:

```bash
touch ~/Library/LaunchAgents/com.user.downloadcleaner.plist
```

### 2. Configure the Service

Paste the following configuration into the file. **Important:** Replace `YOUR_USERNAME` and `/PATH/TO/PROJECT` with your actual system values.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.downloadcleaner</string>

    <key>ProgramArguments</key>
    <array>
        <!-- Path to uv executable -->
        <string>/Users/YOUR_USERNAME/.local/bin/uv</string>
        <string>run</string>
        <!-- Absolute path to main.py -->
        <string>/PATH/TO/PROJECT/download-cleaner/main.py</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/tmp/com.user.downloadcleaner.stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/com.user.downloadcleaner.stderr.log</string>

    <key>WorkingDirectory</key>
    <string>/PATH/TO/PROJECT/download-cleaner</string>
</dict>
</plist>
```

### 3. Load and Start the Service

```bash
launchctl load ~/Library/LaunchAgents/com.user.downloadcleaner.plist
```

### 4. Monitoring

Check the logs to see the magic happening:

```bash
tail -f /tmp/com.user.downloadcleaner.stdout.log
```