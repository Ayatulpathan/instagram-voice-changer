# 🎙️ Bangla Female Real-Time AI Voice Converter (Colab GPU Bridge)

A complete solution for **100% natural, realistic real-time female voice conversion in Bangla** for Instagram, Facebook, Messenger, and WhatsApp calls.

Instead of basic in-browser pitch shifting (which sounds robotic or synthetic), this system uses a **Deep Neural AI Model running on Google Colab's Free T4 GPU** to convert your male voice into an authentic, biological female voice in real-time (~80–120ms total latency).

---

## 🏗️ System Architecture

```text
[Your Microphone] 
       │
       ▼
[Desktop Client (gui_client.py)] 
       │ (Streams audio chunks via WebSocket)
       ▼
[Google Colab (Free T4 GPU)]
       │ (Neural RVC AI converts Male Bangla -> Real Female Bangla)
       ▼
[Desktop Client receives converted voice]
       │
       ▼
[VB-Audio Virtual Cable (CABLE Input)]
       │
       ▼
[Chrome (Instagram / Facebook Web Call)]
       └─> The other person hears an authentic female voice!
```

---

## 🚀 Setup Guide (Takes ~3 Minutes)

### Step 1: Get the Free Virtual Cable (One-time setup)
1. Download **VB-CABLE Driver** from [vb-audio.com/Cable](https://vb-audio.com/Cable/) (100% Free).
2. Extract the zip file, right-click `VBCABLE_Setup_x64.exe`, and click **Run as administrator**.
3. Click **Install Driver** and restart your computer if prompted.
*(This creates a virtual microphone inside Windows).*

---

### Step 2: Start the AI Server on Google Colab (Free)
1. Open [Google Colab](https://colab.research.google.com).
2. Click **Upload** and upload the file:
   `Bangla_Female_Voice_Colab_Server.ipynb` (located in this project folder).
3. In Colab, go to **Runtime** > **Change runtime type** > ensure **T4 GPU** is selected.
4. Click **Runtime** > **Run all** (or run each cell sequentially).
5. In Step 6, Cloudflare Tunnel will start and print a public WebSocket URL:
   ```text
   =================================================================
   🎉 SUCCESS! YOUR COLAB AI SERVER IS LIVE!
   =================================================================
   👉 COPY THIS URL INTO YOUR DESKTOP APP:

       wss://some-random-name.trycloudflare.com/ws
   =================================================================
   ```
6. **Copy that `wss://...` URL**.

---

### Step 3: Launch the Desktop App
1. Inside the `bangla-ai-voice-desktop` folder, double-click **`run.bat`**.
2. The modern control panel will open:
   * **Colab URL**: Paste your copied `wss://...` URL.
   * **Microphone**: Select your real microphone (e.g. Realtek, USB Mic, Headset).
   * **Output**: Select **"CABLE Input (VB-Audio Virtual Cable)"**.
3. Click **🚀 Connect & Start AI Voice**.
4. The status will turn green: `Status: 🟢 Connected! Speaking AI Female Voice`.
5. Speak into your mic — you will see the input and output VU meters reacting!

---

### Step 4: Make an Instagram or Facebook Call
1. Open Google Chrome.
2. Go to **Settings** > **Privacy and Security** > **Site Settings** > **Microphone** (or type `chrome://settings/content/microphone` in the address bar).
3. Set your Default Microphone to:
   👉 **"CABLE Output (VB-Audio Virtual Cable)"**
4. Open [Instagram](https://www.instagram.com) or [Facebook Messenger](https://www.messenger.com).
5. Start any voice or video call! 
   The person on the call will hear the authentic, realistic female AI voice.

---

## 📁 Project Contents

```text
bangla-ai-voice-desktop/
├── Bangla_Female_Voice_Colab_Server.ipynb  # The Colab GPU notebook
├── gui_client.py                           # Modern Windows Desktop GUI
├── run.bat                                 # 1-click Windows launcher
├── requirements.txt                        # Python dependencies
└── README.md                               # Complete setup guide
```
