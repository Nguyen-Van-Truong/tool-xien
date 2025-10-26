document.getElementById("save").addEventListener("click", async () => {
  const val = document.getElementById("base").value.trim();
  if (!val) return alert("Base URL không được trống.");
  try { new URL(val); } catch { return alert("Base URL không hợp lệ."); }
  await chrome.storage.sync.set({ base: val });
  alert("Đã lưu.");
});
