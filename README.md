# Bangla Female Voice Changer for Instagram & Facebook

A real-time, in-browser Male-to-Female voice changer Chrome extension built specifically for **Instagram Web calls (`instagram.com`)**, **Facebook calls (`facebook.com`)**, and **Messenger (`messenger.com`)** with acoustic compensation tailored for Bengali speech phonetics.

---

## 🚀 Features

* **Real-time Live Audio Processing**: Runs directly inside the browser using Web Audio DSP (~21 ms latency, click-free dual-delay pitch shifting).
* **Bypasses Meta's CSP**: Uses Manifest V3 `"world": "MAIN"` script injection, avoiding Content Security Policy blocks common with older extensions.
* **Bangla Acoustic Formant Shaping**:
  * **Chest Resonance Cut (145 Hz)**: Eliminates deep male fundamental frequencies.
  * **Throat Boxiness Scoop (260 Hz)**: Removes low-frequency vocal tract mud.
  * **Female Formant Boost (3,000 Hz)**: Simulates shorter female vocal tract resonances for clear vowels ($আ, ই, এ$).
  * **Breathiness High-Shelf (5,500 Hz)**: Adds natural feminine vocal presence and clarity.
* **Built-in Mic Test Lab**: Allows you to test and hear your voice through headphones before initiating or answering a call.
* **Video Call Compatible**: Preserves camera video tracks and WebRTC negotiation seamlessly.

---

## 📦 How to Install in Google Chrome / Brave / Edge

1. Clone or download this repository.
2. Open your browser and navigate to:
   ```text
   chrome://extensions
   ```
3. Enable **Developer mode** using the toggle switch in the top right corner.
4. Click the **Load unpacked** button in the top left corner.
5. Select this project folder.
6. The extension icon will now appear in your browser's toolbar. Pin it for quick access!

---

## 🎧 How to Test & Use

### Step 1: Self-Test Before Calling
1. Plug in your **headphones** (to prevent microphone audio feedback).
2. Click the extension icon in Chrome.
3. Click **"🎧 Open Mic Test Page (টেস্ট পেজ খুলুন)"**.
4. Click **"Start Live Mic Test"**.
5. Speak in Bangla into your microphone:
   * Try saying: *"হ্যালো, কেমন আছেন? আপনি কি আমার কথা শুনতে পাচ্ছেন?"*
   * Try the different presets: **Natural Female**, **Young Female**, or **Soft Female**.

### Step 2: Make a Call
1. Open [Instagram](https://www.instagram.com) or [Facebook](https://www.facebook.com) / [Messenger](https://www.messenger.com).
2. Go to **Direct Messages (DMs)** or chat and open any conversation.
3. Click the **Audio Call** or **Video Call** icon.
4. The extension automatically intercepts your microphone input and feeds the converted female voice to the person on the other end in real-time.

---

## 🛠️ Project Structure

```text
├── manifest.json         # Chrome Manifest V3 configuration
├── injector.js           # Main world audio hook (getUserMedia & Web Audio DSP)
├── content_isolated.js   # Isolated world storage bridge
├── popup.html            # Extension popup UI
├── popup.js              # Controls, preset management, and communication
├── test_mic.html         # Standalone in-browser test lab with visualizer
└── icons/                # Extension icons (16px, 48px, 128px)
```

---

## 💡 Speaking Tips for Natural Bengali Female Voice

1. **Keep a Steady Volume**: Speak close to your microphone with a relaxed voice.
2. **Avoid Whispering**: Pitch shifters track voiced periodic audio; whispering consists of unvoiced noise that will sound breathy.
3. **Headphones are Mandatory**: Always wear headphones so the speaker audio does not re-enter the microphone.
