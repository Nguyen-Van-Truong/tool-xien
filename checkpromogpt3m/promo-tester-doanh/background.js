// Default a safe base URL on install (you can change in Options)
chrome.runtime.onInstalled.addListener(async () => {
  const { base } = await chrome.storage.sync.get({ base: "" });
  if (!base) await chrome.storage.sync.set({ base: "https://your-test-domain.example/path?promoCode=" });
});
