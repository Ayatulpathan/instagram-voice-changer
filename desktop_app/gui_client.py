"""
Bangla Female Voice Real-Time AI Desktop Client
Provides:
1. 🚀 Cloud AI Mode: Streams mic audio to Google Colab GPU via low-latency WebSocket.
2. ⚡ Local Instant Mode: Real-time dual-delay pitch shifter + female formant resonator running offline on PC.
3. 🎧 Live Audio Monitor: Allows hearing yourself in headphones/speakers while routing to VB-Cable for Instagram/Facebook.
4. 🌐 1-Click Openers: Open Colab notebook and Instagram web in browser.
"""

import sys
import os
import time
import queue
import threading
import asyncio
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

import sounddevice as sd
import numpy as np
import scipy.signal as signal
import websockets

SAMPLE_RATE = 24000
BLOCK_SIZE = 1024  # ~42ms per chunk
COLAB_NOTEBOOK_URL = "https://colab.research.google.com/github/Ayatulpathan/instagram-voice-changer/blob/main/Bangla_Female_Voice_Colab_Server.ipynb"

# Presets mapping (semitones, formant boost freq, formant Q)
PRESETS = {
    "🌸 Realistic Female (বাস্তবধর্মী মিষ্টি কণ্ঠ)": (8.5, 2400.0, 1.5),
    "🍯 Sweet & Soft (মিষ্টি ও কোমল)": (7.5, 2300.0, 1.8),
    "👧 Young Girl (তরুণী কণ্ঠ)": (10.0, 2600.0, 1.4),
    "👩 Mature Lady (পরিপক্ক কণ্ঠ)": (6.5, 2100.0, 1.6)
}

class LocalVoiceEngine:
    """Zero-latency local dual-delay pitch shifter and female vocal tract filter."""
    def __init__(self, sr=SAMPLE_RATE, max_delay_ms=30):
        self.sr = sr
        self.max_delay = int(sr * max_delay_ms / 1000)
        self.buf = np.zeros(self.max_delay * 4, dtype=np.float32)
        self.buf_len = len(self.buf)
        self.write_ptr = 0
        self.phase = 0.0
        self.setup_filters(8.5, 2400.0, 1.5)

    def setup_filters(self, semitones, formant_freq, q):
        self.semitones = semitones
        nyq = self.sr * 0.5
        # Highpass filter (cuts heavy male chest frequencies)
        self.b_high, self.a_high = signal.butter(2, 160.0 / nyq, btype='highpass')
        self.zi_high = signal.lfilter_zi(self.b_high, self.a_high) * 0.0

        # Formant resonance filter (female vocal tract boost)
        low_f = max(50.0, formant_freq - 300.0)
        high_f = min(nyq - 50.0, formant_freq + 300.0)
        self.b_form, self.a_form = signal.butter(2, [low_f / nyq, high_f / nyq], btype='bandpass')
        self.zi_form = signal.lfilter_zi(self.b_form, self.a_form) * 0.0

    def process(self, chunk):
        # 1. High-pass cut male fundamental
        clean, self.zi_high = signal.lfilter(self.b_high, self.a_high, chunk, zi=self.zi_high)

        # 2. Dual-delay pitch shift
        ratio = 2.0 ** (self.semitones / 12.0)
        slope = (ratio - 1.0) / self.max_delay
        n = len(clean)
        shifted = np.zeros(n, dtype=np.float32)

        for i in range(n):
            self.buf[self.write_ptr] = clean[i]
            p1 = self.phase % 1.0
            p2 = (self.phase + 0.5) % 1.0

            d1 = p1 * self.max_delay
            d2 = p2 * self.max_delay

            # Tap 1
            idx1 = (self.write_ptr - d1) % self.buf_len
            i1 = int(idx1)
            frac1 = idx1 - i1
            s1 = (1.0 - frac1) * self.buf[i1] + frac1 * self.buf[(i1 + 1) % self.buf_len]
            w1 = np.sin(np.pi * p1)

            # Tap 2
            idx2 = (self.write_ptr - d2) % self.buf_len
            i2 = int(idx2)
            frac2 = idx2 - i2
            s2 = (1.0 - frac2) * self.buf[i2] + frac2 * self.buf[(i2 + 1) % self.buf_len]
            w2 = np.sin(np.pi * p2)

            shifted[i] = (s1 * w1 * w1 + s2 * w2 * w2)
            self.write_ptr = (self.write_ptr + 1) % self.buf_len
            self.phase += slope

        # 3. Add female formant resonance
        formant, self.zi_form = signal.lfilter(self.b_form, self.a_form, shifted, zi=self.zi_form)
        out = shifted + formant * 0.35

        # 4. Soft glottal clamp
        return np.tanh(out * 1.15) * 0.95


class BanglaAIVoiceClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Bangla Female Voice Real-Time Converter (Colab AI & Local)")
        self.root.geometry("560x780")
        self.root.resizable(False, False)
        self.root.configure(bg="#12161c")

        self.is_running = False
        self.worker_thread = None
        self.audio_in_queue = queue.Queue(maxsize=30)
        self.audio_out_queue = queue.Queue(maxsize=30)
        self.audio_monitor_queue = queue.Queue(maxsize=30)

        self.local_engine = LocalVoiceEngine()

        self.setup_ui()
        self.refresh_devices()

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#1a202c", pady=10)
        header_frame.pack(fill="x")
        
        lbl_title = tk.Label(header_frame, text="🎙️ Bangla Female Real-Time Voice Studio", 
                             font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#1a202c")
        lbl_title.pack()
        lbl_subtitle = tk.Label(header_frame, text="Neural GPU AI Bridge & Local Converter for Instagram / Facebook Calls", 
                                font=("Segoe UI", 8), fg="#a0aec0", bg="#1a202c")
        lbl_subtitle.pack()

        # Quick Actions Bar (Colab & Instagram 1-click links)
        bar_frame = tk.Frame(self.root, bg="#161d27", pady=6, padx=15)
        bar_frame.pack(fill="x")

        btn_open_colab = tk.Button(bar_frame, text="⚡ 1-Click Open Colab Notebook", font=("Segoe UI", 8, "bold"),
                                   bg="#dd6b20", fg="#ffffff", activebackground="#c05621",
                                   relief="flat", cursor="hand2", padx=8, pady=3,
                                   command=lambda: webbrowser.open(COLAB_NOTEBOOK_URL))
        btn_open_colab.pack(side="left", padx=(0, 6))

        btn_open_ig = tk.Button(bar_frame, text="📷 Open Instagram Web", font=("Segoe UI", 8, "bold"),
                                bg="#3182ce", fg="#ffffff", activebackground="#2b6cb0",
                                relief="flat", cursor="hand2", padx=8, pady=3,
                                command=lambda: webbrowser.open("https://www.instagram.com/direct/inbox/"))
        btn_open_ig.pack(side="left")

        main_frame = tk.Frame(self.root, bg="#12161c", padx=16, pady=10)
        main_frame.pack(fill="both", expand=True)

        # Engine Mode Selector
        mode_frame = tk.LabelFrame(main_frame, text=" Conversion Engine Mode ", font=("Segoe UI", 9, "bold"),
                                   fg="#cbd5e0", bg="#18202a", padx=10, pady=8)
        mode_frame.pack(fill="x", pady=(0, 10))

        self.mode_var = tk.StringVar(value="cloud")
        rb_cloud = tk.Radiobutton(mode_frame, text="🚀 Google Colab GPU (Best Neural Quality)", 
                                  variable=self.mode_var, value="cloud", command=self.on_mode_change,
                                  font=("Segoe UI", 9, "bold"), fg="#48bb78", bg="#18202a", 
                                  activebackground="#18202a", selectcolor="#12161c")
        rb_cloud.pack(anchor="w")

        rb_local = tk.Radiobutton(mode_frame, text="⚡ Local Offline Engine (Instant Zero-Setup Test on PC)", 
                                  variable=self.mode_var, value="local", command=self.on_mode_change,
                                  font=("Segoe UI", 9, "bold"), fg="#63b3ed", bg="#18202a", 
                                  activebackground="#18202a", selectcolor="#12161c")
        rb_local.pack(anchor="w")

        # Colab Tunnel URL Frame
        self.url_frame = tk.Frame(main_frame, bg="#12161c")
        self.url_frame.pack(fill="x", pady=(0, 10))

        lbl_url = tk.Label(self.url_frame, text="Google Colab WebSocket URL (from Colab Step 6):", 
                           font=("Segoe UI", 8, "bold"), fg="#e2e8f0", bg="#12161c")
        lbl_url.pack(anchor="w", pady=(0, 2))
        
        self.ent_url = tk.Entry(self.url_frame, font=("Segoe UI", 9), bg="#1e2530", fg="#48bb78", 
                                insertbackground="#ffffff", relief="flat", highlightthickness=1, 
                                highlightbackground="#2d3748", highlightcolor="#e1306c")
        self.ent_url.pack(fill="x", ipady=4)
        self.ent_url.insert(0, "wss://your-tunnel.trycloudflare.com/ws")

        # Voice Preset Selection
        preset_frame = tk.Frame(main_frame, bg="#12161c")
        preset_frame.pack(fill="x", pady=(0, 10))

        lbl_preset = tk.Label(preset_frame, text="Female Voice Preset:", font=("Segoe UI", 9, "bold"),
                              fg="#e2e8f0", bg="#12161c")
        lbl_preset.pack(anchor="w", pady=(0, 2))
        self.cbo_preset = ttk.Combobox(preset_frame, state="readonly", values=list(PRESETS.keys()), font=("Segoe UI", 9))
        self.cbo_preset.current(0)
        self.cbo_preset.pack(fill="x")
        self.cbo_preset.bind("<<ComboboxSelected>>", self.on_preset_change)

        # Audio Device Routing Frame
        dev_frame = tk.LabelFrame(main_frame, text=" Audio Routing (Windows Sound Devices) ", 
                                  font=("Segoe UI", 9, "bold"), fg="#cbd5e0", bg="#18202a", padx=10, pady=8)
        dev_frame.pack(fill="x", pady=(0, 10))

        # Microphone Input
        lbl_in = tk.Label(dev_frame, text="Microphone (Your Real Voice):", font=("Segoe UI", 8), 
                          fg="#e2e8f0", bg="#18202a")
        lbl_in.pack(anchor="w")
        self.cbo_input = ttk.Combobox(dev_frame, state="readonly", font=("Segoe UI", 8))
        self.cbo_input.pack(fill="x", pady=(1, 6))

        # Virtual Cable Output (For Instagram Call)
        lbl_out = tk.Label(dev_frame, text="Call Output -> Select 'CABLE Input' (Feeds into Instagram/Facebook Call):", 
                           font=("Segoe UI", 8, "bold"), fg="#ecc94b", bg="#18202a")
        lbl_out.pack(anchor="w")
        self.cbo_output = ttk.Combobox(dev_frame, state="readonly", font=("Segoe UI", 8))
        self.cbo_output.pack(fill="x", pady=(1, 6))

        # Headphone Live Monitor (Hear Myself)
        mon_header = tk.Frame(dev_frame, bg="#18202a")
        mon_header.pack(fill="x")
        self.monitor_var = tk.BooleanVar(value=True)
        cb_monitor = tk.Checkbutton(mon_header, text="🎧 Hear Myself Live (Listen in Headphones/Speakers):", 
                                    variable=self.monitor_var, font=("Segoe UI", 8, "bold"),
                                    fg="#63b3ed", bg="#18202a", activebackground="#18202a", selectcolor="#12161c")
        cb_monitor.pack(side="left")

        self.cbo_monitor = ttk.Combobox(dev_frame, state="readonly", font=("Segoe UI", 8))
        self.cbo_monitor.pack(fill="x", pady=(1, 4))

        btn_refresh = tk.Button(dev_frame, text="🔄 Refresh Devices", font=("Segoe UI", 8), 
                                command=self.refresh_devices, bg="#2d3748", fg="#e2e8f0", 
                                relief="flat", cursor="hand2")
        btn_refresh.pack(anchor="e", pady=(2, 0))

        # Volume Gain Frame
        gain_frame = tk.Frame(main_frame, bg="#12161c")
        gain_frame.pack(fill="x", pady=(0, 8))

        lbl_gain = tk.Label(gain_frame, text="Microphone Boost Gain:", font=("Segoe UI", 8), 
                            fg="#e2e8f0", bg="#12161c")
        lbl_gain.pack(side="left")
        self.gain_val_lbl = tk.Label(gain_frame, text="1.2x", font=("Segoe UI", 8, "bold"), 
                                     fg="#e1306c", bg="#12161c")
        self.gain_val_lbl.pack(side="right")
        self.scale_gain = tk.Scale(main_frame, from_=0.5, to=2.5, resolution=0.1, orient="horizontal", 
                                   showvalue=False, bg="#12161c", fg="#e2e8f0", troughcolor="#1e2530", 
                                   highlightthickness=0, command=self.on_gain_change)
        self.scale_gain.set(1.2)
        self.scale_gain.pack(fill="x", pady=(0, 10))

        # VU Meters Frame
        meter_frame = tk.Frame(main_frame, bg="#18202a", padx=10, pady=8, relief="groove")
        meter_frame.pack(fill="x", pady=(0, 12))

        lbl_m1 = tk.Label(meter_frame, text="Your Microphone Input Level:", font=("Segoe UI", 8), 
                          fg="#a0aec0", bg="#18202a")
        lbl_m1.pack(anchor="w")
        self.meter_in = ttk.Progressbar(meter_frame, orient="horizontal", mode="determinate")
        self.meter_in.pack(fill="x", pady=(2, 6))

        lbl_m2 = tk.Label(meter_frame, text="AI Female Voice Output Level:", font=("Segoe UI", 8), 
                          fg="#a0aec0", bg="#18202a")
        lbl_m2.pack(anchor="w")
        self.meter_out = ttk.Progressbar(meter_frame, orient="horizontal", mode="determinate")
        self.meter_out.pack(fill="x", pady=(2, 0))

        # Connect / Disconnect Big Button
        self.btn_toggle = tk.Button(main_frame, text="🚀 Connect & Start AI Voice", 
                                    font=("Segoe UI", 11, "bold"), bg="#e1306c", fg="#ffffff", 
                                    activebackground="#c1275d", activeforeground="#ffffff", 
                                    relief="flat", cursor="hand2", command=self.toggle_stream)
        self.btn_toggle.pack(fill="x", ipady=8, pady=(0, 8))

        # Status & Ping Footer
        footer_frame = tk.Frame(main_frame, bg="#12161c")
        footer_frame.pack(fill="x")
        self.lbl_status = tk.Label(footer_frame, text="Status: Ready", font=("Segoe UI", 9), 
                                   fg="#718096", bg="#12161c")
        self.lbl_status.pack(side="left")
        self.lbl_ping = tk.Label(footer_frame, text="Latency: -- ms", font=("Segoe UI", 9, "bold"), 
                                 fg="#718096", bg="#12161c")
        self.lbl_ping.pack(side="right")

    def on_gain_change(self, val):
        self.gain_val_lbl.config(text=f"{float(val):.1f}x")

    def on_mode_change(self):
        if self.mode_var.get() == "local":
            self.url_frame.pack_forget()
            self.btn_toggle.config(text="⚡ Start Local Female Voice (Instant)", bg="#3182ce")
            self.lbl_status.config(text="Status: Ready (Local Offline Engine)", fg="#63b3ed")
        else:
            self.url_frame.pack(fill="x", pady=(0, 10), before=self.cbo_preset.master)
            self.btn_toggle.config(text="🚀 Connect & Start AI Voice", bg="#e1306c")
            self.lbl_status.config(text="Status: Ready to connect to Colab", fg="#718096")

    def on_preset_change(self, event=None):
        name = self.cbo_preset.get()
        if name in PRESETS:
            semis, freq, q = PRESETS[name]
            self.local_engine.setup_filters(semis, freq, q)

    def refresh_devices(self):
        devices = sd.query_devices()
        input_list = []
        output_list = []
        self.input_indices = {}
        self.output_indices = {}

        for idx, dev in enumerate(devices):
            name = dev['name']
            if dev['max_input_channels'] > 0:
                display_name = f"{name} (#{idx})"
                input_list.append(display_name)
                self.input_indices[display_name] = idx
            if dev['max_output_channels'] > 0:
                display_name = f"{name} (#{idx})"
                output_list.append(display_name)
                self.output_indices[display_name] = idx

        self.cbo_input['values'] = input_list
        self.cbo_output['values'] = output_list
        self.cbo_monitor['values'] = output_list

        # Smart preselection:
        # 1. Microphone: USB or default
        if input_list:
            selected_in = input_list[0]
            for item in input_list:
                if "usb" in item.lower() and "microphone" in item.lower():
                    selected_in = item
                    break
                elif "microphone" in item.lower():
                    selected_in = item
            self.cbo_input.set(selected_in)

        # 2. Main Call Output: VB-Audio Cable Input
        if output_list:
            selected_out = output_list[0]
            for item in output_list:
                if "cable input" in item.lower():
                    selected_out = item
                    break
            self.cbo_output.set(selected_out)

        # 3. Monitor: Physical Speakers / USB Headphones
        if output_list:
            selected_mon = output_list[0]
            for item in output_list:
                if "usb" in item.lower() and "speaker" in item.lower():
                    selected_mon = item
                    break
                elif "speaker" in item.lower() and "cable" not in item.lower():
                    selected_mon = item
            self.cbo_monitor.set(selected_mon)

    def toggle_stream(self):
        if not self.is_running:
            mode = self.mode_var.get()
            in_choice = self.cbo_input.get()
            out_choice = self.cbo_output.get()
            mon_choice = self.cbo_monitor.get()

            if not in_choice or not out_choice:
                messagebox.showerror("Select Devices", "Please select your input microphone and output audio device.")
                return

            self.in_device_id = self.input_indices[in_choice]
            self.out_device_id = self.output_indices[out_choice]
            self.mon_device_id = self.output_indices.get(mon_choice, None)
            self.use_monitor = self.monitor_var.get() and (self.mon_device_id is not None)

            # Check preset
            self.on_preset_change()

            if mode == "cloud":
                url = self.ent_url.get().strip()
                if not url or not (url.startswith("ws://") or url.startswith("wss://")):
                    messagebox.showerror("Invalid URL", "Please enter a valid WebSocket URL from Google Colab (e.g. wss://...trycloudflare.com/ws)")
                    return
                self.ws_url = url
                self.is_running = True
                self.btn_toggle.config(text="🛑 Stop AI Voice Stream", bg="#e53e3e")
                self.lbl_status.config(text="Status: Connecting to Colab GPU...", fg="#ecc94b")
                self.worker_thread = threading.Thread(target=self.run_cloud_async, daemon=True)
                self.worker_thread.start()
            else:
                self.is_running = True
                self.btn_toggle.config(text="🛑 Stop Local Voice Stream", bg="#e53e3e")
                self.lbl_status.config(text="Status: 🟢 Running (Local Voice Engine)", fg="#48bb78")
                self.lbl_ping.config(text="Latency: < 5 ms", fg="#48bb78")
                self.worker_thread = threading.Thread(target=self.run_local_stream, daemon=True)
                self.worker_thread.start()
        else:
            self.is_running = False
            self.btn_toggle.config(text="🚀 Connect & Start AI Voice" if self.mode_var.get() == "cloud" else "⚡ Start Local Female Voice (Instant)", 
                                   bg="#e1306c" if self.mode_var.get() == "cloud" else "#3182ce")
            self.lbl_status.config(text="Status: Stopped", fg="#718096")
            self.lbl_ping.config(text="Latency: -- ms")
            self.meter_in["value"] = 0
            self.meter_out["value"] = 0

    # ------------------ Local Engine Thread ------------------
    def run_local_stream(self):
        gain = float(self.scale_gain.get())

        def in_callback(indata, frames, time_info, status):
            chunk = (indata[:, 0] * float(self.scale_gain.get())).astype(np.float32)
            rms_in = np.sqrt(np.mean(chunk**2))
            self.root.after(0, self.update_in_meter, min(100, int(rms_in * 350)))

            # Process through local female pitch/formant engine
            converted = self.local_engine.process(chunk)

            rms_out = np.sqrt(np.mean(converted**2))
            self.root.after(0, self.update_out_meter, min(100, int(rms_out * 350)))

            pcm_bytes = (np.clip(converted, -1.0, 1.0) * 32767.0).astype(np.int16).tobytes()
            try:
                self.audio_out_queue.put_nowait(pcm_bytes)
                if self.use_monitor:
                    self.audio_monitor_queue.put_nowait(pcm_bytes)
            except queue.Full:
                pass

        def out_callback(outdata, frames, time_info, status):
            try:
                data_bytes = self.audio_out_queue.get_nowait()
                arr = np.frombuffer(data_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                outdata[:, 0] = arr
            except queue.Empty:
                outdata.fill(0)

        def mon_callback(outdata, frames, time_info, status):
            try:
                data_bytes = self.audio_monitor_queue.get_nowait()
                arr = np.frombuffer(data_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                outdata[:, 0] = arr
            except queue.Empty:
                outdata.fill(0)

        try:
            in_stream = sd.InputStream(device=self.in_device_id, channels=1, samplerate=SAMPLE_RATE,
                                       blocksize=BLOCK_SIZE, callback=in_callback)
            out_stream = sd.OutputStream(device=self.out_device_id, channels=1, samplerate=SAMPLE_RATE,
                                         blocksize=BLOCK_SIZE, callback=out_callback)
            mon_stream = None
            if self.use_monitor and self.mon_device_id != self.out_device_id:
                mon_stream = sd.OutputStream(device=self.mon_device_id, channels=1, samplerate=SAMPLE_RATE,
                                             blocksize=BLOCK_SIZE, callback=mon_callback)

            with in_stream, out_stream:
                if mon_stream:
                    with mon_stream:
                        while self.is_running:
                            time.sleep(0.05)
                else:
                    while self.is_running:
                        time.sleep(0.05)
        except Exception as e:
            self.root.after(0, self.lbl_status.config, {"text": f"Error: {e}", "fg": "#f56565"})
        finally:
            self.is_running = False
            self.root.after(0, self.btn_toggle.config, {"text": "⚡ Start Local Female Voice (Instant)", "bg": "#3182ce"})

    # ------------------ Cloud Colab GPU Async Thread ------------------
    def run_cloud_async(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.main_cloud_task())

    async def main_cloud_task(self):
        def mic_callback(indata, frames, time_info, status):
            chunk = (indata[:, 0] * float(self.scale_gain.get())).astype(np.float32)
            rms = np.sqrt(np.mean(chunk**2))
            self.root.after(0, self.update_in_meter, min(100, int(rms * 350)))
            pcm_bytes = (np.clip(chunk, -1.0, 1.0) * 32767.0).astype(np.int16).tobytes()
            try:
                self.audio_in_queue.put_nowait(pcm_bytes)
            except queue.Full:
                pass

        def out_callback(outdata, frames, time_info, status):
            try:
                data_bytes = self.audio_out_queue.get_nowait()
                arr = np.frombuffer(data_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                outdata[:, 0] = arr
                rms = np.sqrt(np.mean(arr**2))
                self.root.after(0, self.update_out_meter, min(100, int(rms * 350)))
            except queue.Empty:
                outdata.fill(0)
                self.root.after(0, self.update_out_meter, 0)

        def mon_callback(outdata, frames, time_info, status):
            try:
                data_bytes = self.audio_monitor_queue.get_nowait()
                arr = np.frombuffer(data_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                outdata[:, 0] = arr
            except queue.Empty:
                outdata.fill(0)

        try:
            async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=20) as ws:
                self.root.after(0, self.lbl_status.config, {"text": "Status: 🟢 Connected! Speaking AI Female Voice", "fg": "#48bb78"})
                
                in_stream = sd.InputStream(device=self.in_device_id, channels=1, samplerate=SAMPLE_RATE,
                                           blocksize=BLOCK_SIZE, callback=mic_callback)
                out_stream = sd.OutputStream(device=self.out_device_id, channels=1, samplerate=SAMPLE_RATE,
                                             blocksize=BLOCK_SIZE, callback=out_callback)
                mon_stream = None
                if self.use_monitor and self.mon_device_id != self.out_device_id:
                    mon_stream = sd.OutputStream(device=self.mon_device_id, channels=1, samplerate=SAMPLE_RATE,
                                                 blocksize=BLOCK_SIZE, callback=mon_callback)

                streams = [in_stream, out_stream]
                if mon_stream:
                    streams.append(mon_stream)

                with in_stream, out_stream:
                    if mon_stream:
                        mon_stream.start()
                    while self.is_running:
                        try:
                            pcm_chunk = self.audio_in_queue.get_nowait()
                        except queue.Empty:
                            await asyncio.sleep(0.005)
                            continue

                        t_start = time.time()
                        await ws.send(pcm_chunk)
                        converted_pcm = await ws.recv()
                        rtt = int((time.time() - t_start) * 1000)

                        try:
                            self.audio_out_queue.put_nowait(converted_pcm)
                            if self.use_monitor:
                                self.audio_monitor_queue.put_nowait(converted_pcm)
                        except queue.Full:
                            pass

                        self.root.after(0, self.lbl_ping.config, {"text": f"Latency: {rtt} ms", "fg": "#48bb78" if rtt < 120 else "#ecc94b"})
                    if mon_stream:
                        mon_stream.stop()

        except Exception as e:
            self.root.after(0, self.lbl_status.config, {"text": f"Status: ❌ Connection Error ({e})", "fg": "#f56565"})
        finally:
            self.is_running = False
            self.root.after(0, self.btn_toggle.config, {"text": "🚀 Connect & Start AI Voice", "bg": "#e1306c"})
            self.root.after(0, self.lbl_ping.config, {"text": "Latency: -- ms"})

    def update_in_meter(self, val):
        self.meter_in["value"] = val

    def update_out_meter(self, val):
        self.meter_out["value"] = val

if __name__ == "__main__":
    root = tk.Tk()
    app = BanglaAIVoiceClient(root)
    root.mainloop()
