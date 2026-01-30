(function () {
  const selectors = __CF_SELECTORS__;
  const reportedNodes = new WeakSet();
  let pendingRescan = false;

  function isRealCallbackReady() {
    return (
      typeof window.onCloudflareDetected === "function" &&
      window.onCloudflareDetected.toString().includes("__cf_callback")
    );
  }

  function tryReport(node, sel) {
    if (reportedNodes.has(node)) return;

    if (!isRealCallbackReady()) {
      pendingRescan = true;
      return;
    }

    reportedNodes.add(node);
    try {
      window.onCloudflareDetected(sel, location.href);
    } catch (e) {
      console.error("onCloudflareDetected failed:", e);
    }
  }

  function scan(root) {
    for (const sel of selectors) {
      let nodes;
      try {
        nodes = root.querySelectorAll(sel);
      } catch (e) {
        continue;
      }
      for (const node of nodes) {
        console.log("Found Cloudflare element for selector:", sel, node);
        tryReport(node, sel);
      }
    }
  }

  // Expose function to trigger rescan from Python side
  window.__triggerCfRescan = function() {
    const root = document.body || document.documentElement;
    if (root) {
      scan(root);
    }
  };

  function startObserve() {
    const root = document.body || document.documentElement;
    if (!root) return;

    const observer = new MutationObserver(() => {
      scan(root);
    });

    observer.observe(root, { childList: true, subtree: true });
    scan(root);
  }

  const readyTimer = setInterval(() => {
    if (pendingRescan && isRealCallbackReady()) {
      const root = document.body || document.documentElement;
      if (root) {
        scan(root);
        pendingRescan = false;
      }
    }
  }, 300);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startObserve);
  } else {
    startObserve();
  }
})();
