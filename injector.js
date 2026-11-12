// injector.js (Runs in page MAIN world at document_start)
(() => {
  if (window.__banglaVoiceChangerInstalled) return;
  window.__banglaVoiceChangerInstalled = true;

  console.log("%c[Bangla Voice Changer] Initializing on Instagram & Facebook / Messenger...", "color: #e1306c; font-weight: bold;");

  // --- Real-Time Configuration State ---
  const state = {
    enabled: true,
    semitones: 4.8,         // ~1.32x pitch ratio (optimal for male-to-female)
    formantFreq: 3000,      // Hz (boost female second/third formant resonance)
    lowCutFreq: 145,        // Hz (cut male deep chest fundamental)
    preset: "natural_female",
    // Internal node references for live adjustments
    activePitchShifters: new Set(),
    activeFilters: new Set()
  };

  // Convert semitones to frequency ratio
  function semitonesToRatio(semitones) {
    return Math.pow(2, semitones / 12);
  }

  // --- Dual-Delay Continuous Pitch Shifter ---
  class DualDelayPitchShifter {
    constructor(sampleRate, semitones = 4.8) {
      this.sampleRate = sampleRate || 48000;
      this.ratio = semitonesToRatio(semitones);

      // 25ms grain size gives optimal time/frequency resolution for human speech
      this.grainSize = Math.max(256, Math.floor(this.sampleRate * 0.025));
      this.bufferSize = this.grainSize * 4;
      this.buffer = new Float32Array(this.bufferSize);
      this.writePtr = 0;
      this.phase = 0.0;
    }

    setSemitones(semitones) {
      this.ratio = Math.max(0.6, Math.min(2.0, semitonesToRatio(semitones)));
    }

    process(inputBuffer, outputBuffer) {
      const len = inputBuffer.length;
      const ratio = this.ratio;

      // Bypass mode
      if (Math.abs(ratio - 1.0) < 0.005) {
        outputBuffer.set(inputBuffer);
        return;
      }

      const grainSize = this.grainSize;
      const bufferSize = this.bufferSize;
      const buffer = this.buffer;
      const rampPeriod = grainSize / Math.abs(ratio - 1.0);
      const isPitchUp = ratio > 1.0;

      for (let i = 0; i < len; i++) {
        buffer[this.writePtr] = inputBuffer[i];

        // Two grain phases shifted by 180 degrees
        const p1 = (this.phase / rampPeriod) % 1.0;
        const p2 = ((this.phase + rampPeriod * 0.5) / rampPeriod) % 1.0;

        // If pitch up, delay decreases over time (plays forward faster)
        // If pitch down, delay increases over time
        const delay1 = isPitchUp ? (1.0 - p1) * grainSize : p1 * grainSize;
        const delay2 = isPitchUp ? (1.0 - p2) * grainSize : p2 * grainSize;

        // Hann windows: Hann(p) + Hann(p + 0.5) identically equals 1.0! Zero tremolo / zero clicks.
        const w1 = 0.5 * (1.0 - Math.cos(2.0 * Math.PI * p1));
        const w2 = 0.5 * (1.0 - Math.cos(2.0 * Math.PI * p2));

        // Linear interpolation for read 1
        const r1 = (this.writePtr - delay1 + bufferSize) % bufferSize;
        const idx1 = Math.floor(r1);
        const frac1 = r1 - idx1;
        const next1 = (idx1 + 1) % bufferSize;
        const s1 = buffer[idx1] * (1.0 - frac1) + buffer[next1] * frac1;

        // Linear interpolation for read 2
        const r2 = (this.writePtr - delay2 + bufferSize) % bufferSize;
        const idx2 = Math.floor(r2);
        const frac2 = r2 - idx2;
        const next2 = (idx2 + 1) % bufferSize;
        const s2 = buffer[idx2] * (1.0 - frac2) + buffer[next2] * frac2;

        outputBuffer[i] = s1 * w1 + s2 * w2;

        this.writePtr = (this.writePtr + 1) % bufferSize;
        this.phase += 1.0;
      }
    }
  }

  // --- Listen for configuration messages from Extension Popup ---
  window.addEventListener("message", (event) => {
    if (event.data?.source === "VOICE_CHANGER_EXT" && event.data?.type === "SET_CONFIG") {
      const cfg = event.data.config;
      if (typeof cfg.enabled === "boolean") state.enabled = cfg.enabled;
      if (typeof cfg.semitones === "number") state.semitones = cfg.semitones;
      if (typeof cfg.formantFreq === "number") state.formantFreq = cfg.formantFreq;
      if (typeof cfg.lowCutFreq === "number") state.lowCutFreq = cfg.lowCutFreq;
      if (typeof cfg.preset === "string") state.preset = cfg.preset;

      // Update active pitch shifters in live calls immediately
      state.activePitchShifters.forEach(ps => ps.setSemitones(state.semitones));

      // Update active filter nodes in live calls immediately
      state.activeFilters.forEach(({ highPass, formantF2 }) => {
        if (highPass) highPass.frequency.setValueAtTime(state.lowCutFreq, 0);
        if (formantF2) formantF2.frequency.setValueAtTime(state.formantFreq, 0);
      });

      console.log("[Bangla Voice Changer] Live config updated:", state);
    }
  });

  // --- Monkey-patch navigator.mediaDevices.getUserMedia ---
  if (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === "function") {
    const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);

    navigator.mediaDevices.getUserMedia = async function (constraints) {
      const stream = await originalGetUserMedia(constraints);

      // If audio is not part of this request, return directly
      if (!constraints || !constraints.audio) {
        return stream;
      }

      console.log("%c[Bangla Voice Changer] Intercepting microphone for call!", "color: #10b981; font-weight: bold;");

      try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)({
          latencyHint: "interactive"
        });

        if (audioCtx.state === "suspended") {
          await audioCtx.resume();
        }

        const source = audioCtx.createMediaStreamSource(stream);

        // 1024 buffer size = 21.3ms latency at 48kHz (smooth real-time conversation)
        const scriptNode = audioCtx.createScriptProcessor(1024, 1, 1);
        const pitchShifter = new DualDelayPitchShifter(audioCtx.sampleRate, state.semitones);
        state.activePitchShifters.add(pitchShifter);

        scriptNode.onaudioprocess = (audioEvent) => {
          const input = audioEvent.inputBuffer.getChannelData(0);
          const output = audioEvent.outputBuffer.getChannelData(0);

          if (state.enabled) {
            pitchShifter.process(input, output);
          } else {
            output.set(input); // Bypass mode
          }
        };

        // --- Bengali Female Vocal Tract Shaping Filter Graph ---
        // 1. High-Pass Filter: Cuts male 80-140Hz chest resonance
        const highPass = audioCtx.createBiquadFilter();
        highPass.type = "highpass";
        highPass.frequency.value = state.lowCutFreq;

        // 2. Throat Boxiness Scoop: -4dB cut at 260Hz
        const throatScoop = audioCtx.createBiquadFilter();
        throatScoop.type = "peaking";
        throatScoop.frequency.value = 260;
        throatScoop.Q.value = 1.3;
        throatScoop.gain.value = -4.0;

        // 3. Female Vowel Formant Peak: +4.5dB boost at 2.8kHz - 3.4kHz
        const formantF2 = audioCtx.createBiquadFilter();
        formantF2.type = "peaking";
        formantF2.frequency.value = state.formantFreq;
        formantF2.Q.value = 1.4;
        formantF2.gain.value = 4.5;

        // 4. Breathiness & Air High-Shelf: +3dB boost at 5.5kHz
        const highShelf = audioCtx.createBiquadFilter();
        highShelf.type = "highshelf";
        highShelf.frequency.value = 5500;
        highShelf.gain.value = 3.0;

        // 5. Dynamics Compressor: Limits peak excursions, prevents call clipping
        const compressor = audioCtx.createDynamicsCompressor();
        compressor.threshold.value = -16.0;
        compressor.knee.value = 8.0;
        compressor.ratio.value = 3.5;
        compressor.attack.value = 0.003;
        compressor.release.value = 0.15;

        // 6. Master Makeup Gain
        const makeupGain = audioCtx.createGain();
        makeupGain.gain.value = 1.2;

        const filterRecord = { highPass, formantF2 };
        state.activeFilters.add(filterRecord);

        // Connect Web Audio Nodes
        source.connect(scriptNode);
        scriptNode.connect(highPass);
        highPass.connect(throatScoop);
        throatScoop.connect(formantF2);
        formantF2.connect(highShelf);
        highShelf.connect(compressor);
        compressor.connect(makeupGain);

        const destination = audioCtx.createMediaStreamDestination();
        makeupGain.connect(destination);

        // Manage lifecycle and track cleanup
        const rawAudioTrack = stream.getAudioTracks()[0];
        const processedAudioTrack = destination.stream.getAudioTracks()[0];

        // Clean up memory and nodes when track is stopped
        rawAudioTrack.addEventListener("ended", () => {
          try {
            state.activePitchShifters.delete(pitchShifter);
            state.activeFilters.delete(filterRecord);
            scriptNode.disconnect();
            audioCtx.close();
          } catch (e) {}
        });

        // Mirror mute/unmute state from original track
        processedAudioTrack.enabled = rawAudioTrack.enabled;
        rawAudioTrack.addEventListener("mute", () => { processedAudioTrack.enabled = false; });
        rawAudioTrack.addEventListener("unmute", () => { processedAudioTrack.enabled = true; });

        // Combine processed audio with original video tracks (for Video Calls)
        const outputStream = new MediaStream([
          processedAudioTrack,
          ...stream.getVideoTracks()
        ]);

        return outputStream;
      } catch (err) {
        console.error("[Bangla Voice Changer] Audio graph error, using original stream:", err);
        return stream;
      }
    };
  }
})();
