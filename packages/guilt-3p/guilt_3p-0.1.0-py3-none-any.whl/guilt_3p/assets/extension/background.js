// Send URL to Python server
function sendUrlToPython(url) {
  fetch("http://localhost:5000/update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: url })
  }).catch(err => console.log("Python script not running"));
}

// Listen for tab switches
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (tab.url) sendUrlToPython(tab.url);
  } catch (e) {}
});

// Listen for URL changes inside the same tab
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    sendUrlToPython(tab.url);
  }
});