_VISUAL_CURSOR_JS = """
(() => {
  if (window.__pw_visual_cursor) return;
  window.__pw_visual_cursor = true;

  /* ----------------------------
   * State
   * ---------------------------- */
  window.__pw_mouse_track = [];

  /* ----------------------------
   * Cursor (red circular dot)
   * ---------------------------- */
  const cursor = document.createElement("div");
  cursor.id = "__pw_cursor";

  Object.assign(cursor.style, {
    position: "fixed",
    top: "0",
    left: "0",
    width: "10px",
    height: "10px",
    pointerEvents: "none",
    zIndex: "2147483647",
    transform: "translate(-5px, -5px)",
    background: "rgba(255, 0, 0, 0.95)",
    borderRadius: "50%",
    boxShadow: "0 0 6px rgba(255, 0, 0, 0.6)",
  });

  /* ----------------------------
   * Canvas for trajectory
   * ---------------------------- */
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  Object.assign(canvas.style, {
    position: "fixed",
    top: "0",
    left: "0",
    pointerEvents: "none",
    zIndex: "2147483646",
  });

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  function drawTrack() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const t = window.__pw_mouse_track;
    if (t.length < 2) return;

    ctx.strokeStyle = "rgba(0,120,255,0.6)";
    ctx.lineWidth = 2;
    ctx.lineCap = "round";

    ctx.beginPath();
    ctx.moveTo(t[0].x, t[0].y);
    for (let i = 1; i < t.length; i++) {
      ctx.lineTo(t[i].x, t[i].y);
    }
    ctx.stroke();
  }

  /* ----------------------------
   * Public API
   * ---------------------------- */
  window.__pw_reset_track = () => {
    window.__pw_mouse_track.length = 0;
    drawTrack();
  };

  window.__pw_move_cursor = (x, y) => {
    if (window.__pw_mouse_track.length === 0) {
      window.__pw_mouse_track.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
      });
    }

    cursor.style.transform = `translate(${x}px, ${y}px)`;
    window.__pw_mouse_track.push({ x, y });
    drawTrack();
  };

  /* ----------------------------
   * Attach
   * ---------------------------- */
  function attach() {
    if (!document.body) {
      requestAnimationFrame(attach);
      return;
    }
    document.body.appendChild(canvas);
    document.body.appendChild(cursor);
  }

  attach();
})();
"""