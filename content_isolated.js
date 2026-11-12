// content_isolated.js (Runs in ISOLATED world)
(() => {
  // 1. Fetch saved configuration from chrome.storage and forward to MAIN world
  try {
    chrome.storage.local.get(["voiceConfig"], (result) => {
      if (result && result.voiceConfig) {
        window.postMessage({
          source: "VOICE_CHANGER_EXT",
          type: "SET_CONFIG",
          config: result.voiceConfig
        }, "*");
      }
    });
  } catch (e) {
    console.warn("[VoiceChanger] Storage access error:", e);
  }

  // 2. Listen for real-time config updates from popup.js and relay to MAIN world
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message && message.source === "VOICE_CHANGER_POPUP") {
      window.postMessage({
        source: "VOICE_CHANGER_EXT",
        type: "SET_CONFIG",
        config: message.config
      }, "*");
      sendResponse({ status: "delivered" });
    }
    return true;
  });
})();
