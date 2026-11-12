// popup.js
document.addEventListener("DOMContentLoaded", () => {
  // --- UI Elements ---
  const masterToggle = document.getElementById("masterToggle");
  const presetButtons = document.querySelectorAll(".preset-btn");
  const semitoneSlider = document.getElementById("semitoneSlider");
  const formantSlider = document.getElementById("formantSlider");
  const lowCutSlider = document.getElementById("lowCutSlider");
  const semitoneVal = document.getElementById("semitoneVal");
  const formantVal = document.getElementById("formantVal");
  const lowCutVal = document.getElementById("lowCutVal");
  const openTestPageBtn = document.getElementById("openTestPageBtn");

  // --- Preset Definitions ---
  const PRESETS = {
    natural_female: { semitones: 4.8, formantFreq: 3000, lowCutFreq: 145 },
    young_female:   { semitones: 5.8, formantFreq: 3400, lowCutFreq: 160 },
    soft_female:    { semitones: 3.8, formantFreq: 2700, lowCutFreq: 135 },
    custom:         null
  };

  let config = {
    enabled: true,
    preset: "natural_female",
    semitones: 4.8,
    formantFreq: 3000,
    lowCutFreq: 145
  };

  // --- Load Saved Settings ---
  chrome.storage.local.get(["voiceConfig"], (result) => {
    if (result && result.voiceConfig) {
      config = { ...config, ...result.voiceConfig };
    }
    updateUI();
  });

  function updateUI() {
    masterToggle.checked = config.enabled;
    semitoneSlider.value = config.semitones;
    formantSlider.value = config.formantFreq;
    lowCutSlider.value = config.lowCutFreq;

    semitoneVal.innerText = `+${parseFloat(config.semitones).toFixed(1)} st`;
    formantVal.innerText = `${config.formantFreq} Hz`;
    lowCutVal.innerText = `${config.lowCutFreq} Hz`;

    presetButtons.forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.preset === config.preset);
    });
  }

  // --- Broadcast to All Instagram, Facebook, and Messenger Tabs ---
  function broadcastConfig() {
    chrome.storage.local.set({ voiceConfig: config });

    const targetUrls = [
      "*://*.instagram.com/*",
      "*://*.facebook.com/*",
      "*://*.messenger.com/*"
    ];

    chrome.tabs.query({ url: targetUrls }, (tabs) => {
      if (tabs && tabs.length > 0) {
        tabs.forEach((tab) => {
          chrome.tabs.sendMessage(tab.id, {
            source: "VOICE_CHANGER_POPUP",
            config: config
          }, () => {
            if (chrome.runtime.lastError) {}
          });
        });
      }
    });
  }

  // --- Event Listeners ---
  masterToggle.addEventListener("change", (e) => {
    config.enabled = e.target.checked;
    broadcastConfig();
  });

  presetButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const pName = btn.dataset.preset;
      config.preset = pName;
      if (PRESETS[pName]) {
        config.semitones = PRESETS[pName].semitones;
        config.formantFreq = PRESETS[pName].formantFreq;
        config.lowCutFreq = PRESETS[pName].lowCutFreq;
      }
      updateUI();
      broadcastConfig();
    });
  });

  semitoneSlider.addEventListener("input", (e) => {
    config.semitones = parseFloat(e.target.value);
    config.preset = "custom";
    updateUI();
    broadcastConfig();
  });

  formantSlider.addEventListener("input", (e) => {
    config.formantFreq = parseInt(e.target.value, 10);
    config.preset = "custom";
    updateUI();
    broadcastConfig();
  });

  lowCutSlider.addEventListener("input", (e) => {
    config.lowCutFreq = parseInt(e.target.value, 10);
    config.preset = "custom";
    updateUI();
    broadcastConfig();
  });

  openTestPageBtn.addEventListener("click", () => {
    chrome.tabs.create({ url: "test_mic.html" });
  });
});
