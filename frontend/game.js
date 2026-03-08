// Star Office UI main game runtime.
// Depends on layout.js being loaded first.

let supportsWebP = false;

function checkWebPSupport() {
  return new Promise((resolve) => {
    const canvas = document.createElement("canvas");
    if (!canvas.getContext || !canvas.getContext("2d")) {
      resolve(false);
      return;
    }
    resolve(canvas.toDataURL("image/webp").indexOf("data:image/webp") === 0);
  });
}

function checkWebPSupportFallback() {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(true);
    img.onerror = () => resolve(false);
    img.src = "data:image/webp;base64,UklGRkoAAABXRUJQVlA4WAoAAAAQAAAAAAAAAAAAQUxQSAwAAAABBxAR/Q9ERP8DAABWUDggGAAAADABAJ0BKgEAAQADADQlpAADcAD++/1QAA==";
  });
}

function getExt(pngFile) {
  if (pngFile === "star-working-spritesheet.png") {
    return ".png";
  }
  if (LAYOUT.forcePng && LAYOUT.forcePng[pngFile.replace(/\.(png|webp)$/, "")]) {
    return ".png";
  }
  return supportsWebP ? ".webp" : ".png";
}

const STATES = {
  standby: { label: "Standing By", area: "lounge" },
  working: { label: "Working", area: "workzone" },
  research: { label: "Researching", area: "workzone" },
  running: { label: "Running", area: "workzone" },
  sync: { label: "Syncing", area: "workzone" },
  incident: { label: "Incident", area: "incident_bay" }
};

const LEGACY_STATE_MAP = {
  idle: "standby",
  writing: "working",
  researching: "research",
  executing: "running",
  syncing: "sync",
  error: "incident"
};

const BUBBLE_TEXTS = {
  standby: [
    "Monitoring queue and staying ready.",
    "Standing by for the next task.",
    "Everything looks stable right now."
  ],
  working: [
    "Heads-down on the active task.",
    "Pushing this workstream forward.",
    "Shipping the next chunk now."
  ],
  research: [
    "Collecting signals and evidence.",
    "Verifying assumptions before coding.",
    "Turning findings into decisions."
  ],
  running: [
    "Executing the plan step-by-step.",
    "Running the pipeline now.",
    "Driving this to completion."
  ],
  sync: [
    "Sync in progress.",
    "Writing updates to shared state.",
    "Aligning all systems now."
  ],
  incident: [
    "Incident triage in progress.",
    "Stabilizing first, root cause next.",
    "Analyzing logs and reducing impact."
  ],
  cat: [
    "Meow.",
    "All clear in the office.",
    "Quality inspector on patrol."
  ]
};

const STATUS_COLOR = {
  approved: "#22c55e",
  pending: "#f59e0b",
  rejected: "#ef4444",
  offline: "#94a3b8"
};

const config = {
  type: Phaser.AUTO,
  width: LAYOUT.game.width,
  height: LAYOUT.game.height,
  parent: "game-container",
  pixelArt: true,
  physics: {
    default: "arcade",
    arcade: { gravity: { y: 0 }, debug: false }
  },
  scene: {
    preload,
    create,
    update
  }
};

const FETCH_INTERVAL = 2000;
const AGENTS_INTERVAL = 2500;
const BUBBLE_INTERVAL = 8000;
const CAT_BUBBLE_INTERVAL = 18000;

let game;
let star;
let sofa;
let serverroom;
let syncAnimSprite;
let errorBug;
let starWorking;
let statusText;
let currentState = "standby";
let bubble = null;
let catBubble = null;
let lastFetch = 0;
let lastAgentsFetch = 0;
let lastBubble = 0;
let lastCatBubble = 0;
let showCoords = false;
let coordsOverlay;
let coordsDisplay;
let coordsToggle;
let guestAgents = [];
let guestSprites = {};

function normalizeState(raw) {
  const text = String(raw || "").trim().toLowerCase();
  if (STATES[text]) return text;
  if (LEGACY_STATE_MAP[text]) return LEGACY_STATE_MAP[text];
  return "standby";
}

function stateToArea(state) {
  return STATES[state]?.area || "lounge";
}

function randomText(bucket) {
  const list = BUBBLE_TEXTS[bucket] || [];
  if (!list.length) return "";
  return list[Math.floor(Math.random() * list.length)];
}

async function loadMemo() {
  const memoDate = document.getElementById("memo-date");
  const memoContent = document.getElementById("memo-content");
  try {
    const response = await fetch("/memo/yesterday?t=" + Date.now(), { cache: "no-store" });
    const data = await response.json();
    if (data.success && data.memo) {
      memoDate.textContent = data.date || "";
      memoContent.innerHTML = data.memo.replace(/\n/g, "<br>");
      return;
    }
    memoContent.innerHTML = '<div id="memo-placeholder">No memo available yet.</div>';
  } catch (error) {
    console.error("Failed to load memo:", error);
    memoContent.innerHTML = '<div id="memo-placeholder">Failed to load memo.</div>';
  }
}

function setStatusLine(text) {
  if (!statusText) return;
  statusText.textContent = text;
}

function updateLoadingProgress(loaded, total) {
  const progressBar = document.getElementById("loading-progress-bar");
  const loadingText = document.getElementById("loading-text");
  const percent = Math.min(100, Math.round((loaded / total) * 100));
  if (progressBar) progressBar.style.width = percent + "%";
  if (loadingText) loadingText.textContent = `Loading Star Lobster Office... ${percent}%`;
}

function hideLoadingOverlay() {
  const loadingOverlay = document.getElementById("loading-overlay");
  if (!loadingOverlay) return;
  loadingOverlay.style.transition = "opacity 0.35s ease";
  loadingOverlay.style.opacity = "0";
  setTimeout(() => {
    loadingOverlay.style.display = "none";
  }, 350);
}

function validateRequiredAssets(scene) {
  const required = [
    "office_bg",
    "star_idle",
    "star_researching",
    "sofa_busy",
    "sofa_idle",
    "serverroom",
    "star_working",
    "error_bug",
    "sync_anim",
    "cats",
    "desk_v2",
    "flowers"
  ];

  const missing = required.filter((key) => !scene.textures.exists(key));
  if (!missing.length) return true;

  const message = "Missing assets after preload: " + missing.join(", ");
  console.error(message);
  setStatusLine(message);
  return false;
}

function setState(state, detail) {
  fetch("/state", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state, detail })
  })
    .then(() => fetchState())
    .catch((error) => {
      console.error("Failed to set state:", error);
      setStatusLine("Unable to update state right now.");
    });
}
window.setState = setState;

function preload() {
  let loadedAssets = 0;
  const totalAssets = LAYOUT.totalAssets || 15;

  this.load.on("filecomplete", () => {
    loadedAssets += 1;
    updateLoadingProgress(loadedAssets, totalAssets);
  });

  this.load.on("complete", () => {
    hideLoadingOverlay();
  });

  this.load.image("office_bg", "/static/office_bg_small" + (supportsWebP ? ".webp" : ".png") + "?v={{VERSION_TIMESTAMP}}");
  this.load.spritesheet("star_idle", "/static/star-idle-spritesheet" + getExt("star-idle-spritesheet.png"), { frameWidth: 128, frameHeight: 128 });
  this.load.spritesheet("star_researching", "/static/star-researching-spritesheet" + getExt("star-researching-spritesheet.png"), { frameWidth: 128, frameHeight: 105 });
  this.load.image("sofa_idle", "/static/sofa-idle" + getExt("sofa-idle.png"));
  this.load.spritesheet("sofa_busy", "/static/sofa-busy-spritesheet" + getExt("sofa-busy-spritesheet.png"), { frameWidth: 256, frameHeight: 256 });
  this.load.spritesheet("serverroom", "/static/serverroom-spritesheet" + getExt("serverroom-spritesheet.png"), { frameWidth: 180, frameHeight: 251 });
  this.load.spritesheet("error_bug", "/static/error-bug-spritesheet-grid" + (supportsWebP ? ".webp" : ".png"), { frameWidth: 180, frameHeight: 180 });
  this.load.spritesheet("sync_anim", "/static/sync-animation-spritesheet-grid" + (supportsWebP ? ".webp" : ".png"), { frameWidth: 256, frameHeight: 256 });
  this.load.spritesheet("star_working", "/static/star-working-spritesheet-grid" + (supportsWebP ? ".webp" : ".png"), { frameWidth: 230, frameHeight: 144 });
  this.load.spritesheet("cats", "/static/cats-spritesheet" + (supportsWebP ? ".webp" : ".png"), { frameWidth: 160, frameHeight: 160 });
  this.load.image("desk_v2", "/static/desk-v2.png");
  this.load.spritesheet("flowers", "/static/flowers-spritesheet" + (supportsWebP ? ".webp" : ".png"), { frameWidth: 65, frameHeight: 65 });
  this.load.spritesheet("plants", "/static/plants-spritesheet" + getExt("plants-spritesheet.png"), { frameWidth: 160, frameHeight: 160 });
  this.load.spritesheet("posters", "/static/posters-spritesheet" + getExt("posters-spritesheet.png"), { frameWidth: 160, frameHeight: 160 });
  this.load.spritesheet("coffee_machine", "/static/coffee-machine-spritesheet" + getExt("coffee-machine-spritesheet.png"), { frameWidth: 230, frameHeight: 230 });
}

function create() {
  game = this;
  statusText = document.getElementById("status-text");
  coordsOverlay = document.getElementById("coords-overlay");
  coordsDisplay = document.getElementById("coords-display");
  coordsToggle = document.getElementById("coords-toggle");

  if (!validateRequiredAssets(this)) {
    return;
  }

  this.add.image(640, 360, "office_bg");

  sofa = this.add.sprite(
    LAYOUT.furniture.sofa.x,
    LAYOUT.furniture.sofa.y,
    "sofa_busy"
  ).setOrigin(LAYOUT.furniture.sofa.origin.x, LAYOUT.furniture.sofa.origin.y).setDepth(LAYOUT.furniture.sofa.depth);

  this.anims.create({ key: "sofa_busy", frames: this.anims.generateFrameNumbers("sofa_busy", { start: 0, end: 47 }), frameRate: 12, repeat: -1 });
  this.anims.create({ key: "star_idle", frames: this.anims.generateFrameNumbers("star_idle", { start: 0, end: 29 }), frameRate: 12, repeat: -1 });
  this.anims.create({ key: "star_researching", frames: this.anims.generateFrameNumbers("star_researching", { start: 0, end: 95 }), frameRate: 12, repeat: -1 });
  this.anims.create({ key: "star_working", frames: this.anims.generateFrameNumbers("star_working", { start: 0, end: 191 }), frameRate: 12, repeat: -1 });
  this.anims.create({ key: "serverroom_on", frames: this.anims.generateFrameNumbers("serverroom", { start: 0, end: 39 }), frameRate: 6, repeat: -1 });
  this.anims.create({ key: "error_bug", frames: this.anims.generateFrameNumbers("error_bug", { start: 0, end: 95 }), frameRate: 12, repeat: -1 });
  this.anims.create({ key: "sync_anim", frames: this.anims.generateFrameNumbers("sync_anim", { start: 1, end: 52 }), frameRate: 12, repeat: -1 });

  this.add.image(LAYOUT.furniture.desk.x, LAYOUT.furniture.desk.y, "desk_v2")
    .setOrigin(0.5, 0.5)
    .setDepth(LAYOUT.furniture.desk.depth);

  const flower = this.add.sprite(LAYOUT.furniture.flower.x, LAYOUT.furniture.flower.y, "flowers", 0)
    .setOrigin(0.5, 0.5)
    .setDepth(LAYOUT.furniture.flower.depth);
  flower.setInteractive({ useHandCursor: true });
  flower.on("pointerdown", () => {
    flower.setFrame(Math.floor(Math.random() * 16));
  });

  serverroom = this.add.sprite(LAYOUT.furniture.serverroom.x, LAYOUT.furniture.serverroom.y, "serverroom", 0)
    .setOrigin(0.5, 0.5)
    .setDepth(LAYOUT.furniture.serverroom.depth);

  errorBug = this.add.sprite(LAYOUT.furniture.errorBug.x, LAYOUT.furniture.errorBug.y, "error_bug", 0)
    .setOrigin(0.5, 0.5)
    .setDepth(LAYOUT.furniture.errorBug.depth)
    .setScale(LAYOUT.furniture.errorBug.scale)
    .setVisible(false);
  errorBug.anims.play("error_bug", true);

  syncAnimSprite = this.add.sprite(LAYOUT.furniture.syncAnim.x, LAYOUT.furniture.syncAnim.y, "sync_anim", 0)
    .setOrigin(0.5, 0.5)
    .setDepth(LAYOUT.furniture.syncAnim.depth);
  syncAnimSprite.anims.stop();

  star = this.add.sprite(LAYOUT.areas.lounge.x, LAYOUT.areas.lounge.y, "star_idle")
    .setOrigin(0.5)
    .setScale(1.35)
    .setDepth(30);

  starWorking = this.add.sprite(LAYOUT.furniture.starWorking.x, LAYOUT.furniture.starWorking.y, "star_working", 0)
    .setOrigin(0.5, 0.5)
    .setScale(LAYOUT.furniture.starWorking.scale)
    .setDepth(LAYOUT.furniture.starWorking.depth)
    .setVisible(false);

  const plaqueBg = this.add.rectangle(LAYOUT.plaque.x, LAYOUT.plaque.y, LAYOUT.plaque.width, LAYOUT.plaque.height, 0x5d4037);
  plaqueBg.setStrokeStyle(3, 0x3e2723);
  this.add.text(LAYOUT.plaque.x, LAYOUT.plaque.y, "Star Lobster Office", {
    fontFamily: "ArkPixel, monospace",
    fontSize: "18px",
    fill: "#ffd700",
    stroke: "#000",
    strokeThickness: 2
  }).setOrigin(0.5).setDepth(2100);

  const cat = this.add.sprite(LAYOUT.furniture.cat.x, LAYOUT.furniture.cat.y, "cats", 0)
    .setOrigin(LAYOUT.furniture.cat.origin.x, LAYOUT.furniture.cat.origin.y)
    .setDepth(LAYOUT.furniture.cat.depth);
  cat.setInteractive({ useHandCursor: true });
  cat.on("pointerdown", () => {
    cat.setFrame(Math.floor(Math.random() * 16));
  });

  coordsToggle.addEventListener("click", () => {
    showCoords = !showCoords;
    coordsOverlay.style.display = showCoords ? "block" : "none";
    coordsToggle.textContent = showCoords ? "Hide Coords" : "Show Coords";
  });

  this.input.on("pointermove", (pointer) => {
    if (!showCoords) return;
    coordsDisplay.textContent = `${Math.round(pointer.x)}, ${Math.round(pointer.y)}`;
    coordsOverlay.style.left = pointer.x + 12 + "px";
    coordsOverlay.style.top = pointer.y + 12 + "px";
  });

  loadMemo();
  fetchState();
  fetchAgents();
}

function applyStateVisuals(state) {
  const area = stateToArea(state);
  const target = LAYOUT.areas[area] || LAYOUT.areas.lounge;

  setStatusLine(`[${STATES[state].label}] ${randomText(state)}`);

  if (state === "standby") {
    star.setVisible(true);
    starWorking.setVisible(false);
    star.setPosition(target.x, target.y);
    star.anims.play("star_idle", true);
    sofa.setTexture("sofa_busy");
    sofa.anims.play("sofa_busy", true);
  } else if (state === "research") {
    star.setVisible(true);
    starWorking.setVisible(false);
    star.setPosition(target.x, target.y);
    star.anims.play("star_researching", true);
    sofa.anims.stop();
    sofa.setTexture("sofa_idle");
  } else {
    star.setVisible(false);
    starWorking.setVisible(true);
    starWorking.anims.play("star_working", true);
    sofa.anims.stop();
    sofa.setTexture("sofa_idle");
  }

  if (state === "sync") {
    if (!syncAnimSprite.anims.isPlaying) syncAnimSprite.anims.play("sync_anim", true);
  } else {
    if (syncAnimSprite.anims.isPlaying) syncAnimSprite.anims.stop();
    syncAnimSprite.setFrame(0);
  }

  if (state === "incident") {
    errorBug.setVisible(true);
  } else {
    errorBug.setVisible(false);
  }

  if (state === "standby") {
    serverroom.anims.stop();
    serverroom.setFrame(0);
  } else {
    serverroom.anims.play("serverroom_on", true);
  }
}

function fetchState() {
  fetch("/state?t=" + Date.now(), { cache: "no-store" })
    .then((response) => response.json())
    .then((data) => {
      const next = normalizeState(data.state);
      currentState = next;
      applyStateVisuals(next);
      const detail = (data.detail || "").trim();
      if (detail) {
        setStatusLine(`[${STATES[next].label}] ${detail}`);
      }
    })
    .catch((error) => {
      console.error("State fetch failed:", error);
      setStatusLine("Connection issue. Retrying...");
    });
}

function renderGuestAgentList() {
  const list = document.getElementById("guest-agent-list");
  if (!list) return;

  if (!guestAgents.length) {
    list.innerHTML = '<div class="empty-list">No guest agents connected.</div>';
    return;
  }

  list.innerHTML = guestAgents.map((agent) => {
    const status = agent.authStatus || "pending";
    const state = normalizeState(agent.state);
    const statusLabel = status.charAt(0).toUpperCase() + status.slice(1);
    const stateLabel = STATES[state]?.label || state;
    return `
      <div class="guest-item">
        <div class="guest-main">
          <div class="guest-name">${agent.name || "Guest Agent"}</div>
          <div class="guest-sub">${statusLabel} - ${stateLabel}</div>
        </div>
        <button class="leave-btn" onclick="leaveGuest('${agent.agentId}', '${(agent.name || "").replace(/'/g, "\\'")}')">Remove</button>
      </div>
    `;
  }).join("");
}

function getAgentPoint(index, area) {
  const slots = {
    lounge: [
      { x: 620, y: 180 },
      { x: 560, y: 220 },
      { x: 680, y: 210 }
    ],
    workzone: [
      { x: 760, y: 320 },
      { x: 830, y: 280 },
      { x: 690, y: 350 }
    ],
    incident_bay: [
      { x: 180, y: 260 },
      { x: 120, y: 220 },
      { x: 240, y: 230 }
    ]
  };
  const points = slots[area] || slots.lounge;
  return points[index % points.length];
}

function renderGuestAgentsInScene() {
  if (!game) return;

  const seen = new Set();
  let index = 0;

  guestAgents.forEach((agent) => {
    if (agent.isMain) return;

    const id = agent.agentId;
    seen.add(id);

    const state = normalizeState(agent.state);
    const area = agent.area || stateToArea(state);
    const point = getAgentPoint(index, area);
    index += 1;

    if (!guestSprites[id]) {
      const icon = game.add.text(point.x, point.y, "🦞", {
        fontFamily: "ArkPixel, monospace",
        fontSize: "24px"
      }).setOrigin(0.5).setDepth(2200);

      const name = game.add.text(point.x, point.y - 28, agent.name || "Guest", {
        fontFamily: "ArkPixel, monospace",
        fontSize: "13px",
        fill: STATUS_COLOR[agent.authStatus] || "#ffffff",
        stroke: "#000",
        strokeThickness: 2
      }).setOrigin(0.5).setDepth(2201);

      guestSprites[id] = { icon, name };
    } else {
      const sprite = guestSprites[id];
      sprite.icon.setPosition(point.x, point.y);
      sprite.name.setPosition(point.x, point.y - 28);
      sprite.name.setText(agent.name || "Guest");
      sprite.name.setColor(STATUS_COLOR[agent.authStatus] || "#ffffff");
    }
  });

  Object.keys(guestSprites).forEach((id) => {
    if (seen.has(id)) return;
    guestSprites[id].icon.destroy();
    guestSprites[id].name.destroy();
    delete guestSprites[id];
  });
}

function leaveGuest(agentId, name) {
  fetch("/agents/leave", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agentId, name })
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.ok) {
        fetchAgents();
        return;
      }
      alert(data.msg || "Unable to remove agent.");
    })
    .catch((error) => {
      console.error("Leave request failed:", error);
      alert("Request failed.");
    });
}
window.leaveGuest = leaveGuest;

function fetchAgents() {
  fetch("/agents?t=" + Date.now(), { cache: "no-store" })
    .then((response) => response.json())
    .then((data) => {
      if (!Array.isArray(data)) return;
      guestAgents = data.filter((agent) => !agent.isMain);
      renderGuestAgentList();
      renderGuestAgentsInScene();
    })
    .catch((error) => {
      console.error("Agent fetch failed:", error);
    });
}

function showBubble() {
  if (!game) return;
  if (bubble) {
    bubble.destroy();
    bubble = null;
  }

  const text = randomText(currentState);
  if (!text || currentState === "standby") return;

  const anchor = starWorking.visible ? starWorking : star;
  const y = anchor.y - 80;
  const bg = game.add.rectangle(anchor.x, y, text.length * 7 + 26, 30, 0xffffff, 0.95);
  bg.setStrokeStyle(2, 0x111111);
  const txt = game.add.text(anchor.x, y, text, {
    fontFamily: "ArkPixel, monospace",
    fontSize: "12px",
    fill: "#111"
  }).setOrigin(0.5);

  bubble = game.add.container(0, 0, [bg, txt]).setDepth(2400);
  setTimeout(() => {
    if (!bubble) return;
    bubble.destroy();
    bubble = null;
  }, 3200);
}

function showCatBubble() {
  if (!game) return;
  if (catBubble) {
    catBubble.destroy();
    catBubble = null;
  }

  const text = randomText("cat");
  const x = LAYOUT.furniture.cat.x;
  const y = LAYOUT.furniture.cat.y - 70;
  const bg = game.add.rectangle(x, y, text.length * 7 + 20, 24, 0xfffbeb, 0.95);
  bg.setStrokeStyle(2, 0xd4a574);
  const txt = game.add.text(x, y, text, {
    fontFamily: "ArkPixel, monospace",
    fontSize: "11px",
    fill: "#8b6914"
  }).setOrigin(0.5);

  catBubble = game.add.container(0, 0, [bg, txt]).setDepth(2600);
  setTimeout(() => {
    if (!catBubble) return;
    catBubble.destroy();
    catBubble = null;
  }, 3800);
}

function update(time) {
  if (time - lastFetch > FETCH_INTERVAL) {
    fetchState();
    lastFetch = time;
  }
  if (time - lastAgentsFetch > AGENTS_INTERVAL) {
    fetchAgents();
    lastAgentsFetch = time;
  }
  if (time - lastBubble > BUBBLE_INTERVAL) {
    showBubble();
    lastBubble = time;
  }
  if (time - lastCatBubble > CAT_BUBBLE_INTERVAL) {
    showCatBubble();
    lastCatBubble = time;
  }

  if (errorBug && errorBug.visible) {
    const range = LAYOUT.furniture.errorBug.pingPong;
    if (!errorBug._direction) errorBug._direction = 1;
    errorBug.x += range.speed * errorBug._direction;
    if (errorBug.x >= range.rightX) errorBug._direction = -1;
    if (errorBug.x <= range.leftX) errorBug._direction = 1;
  }
}

async function initGame() {
  try {
    supportsWebP = await checkWebPSupport();
  } catch (error) {
    try {
      supportsWebP = await checkWebPSupportFallback();
    } catch (fallbackError) {
      supportsWebP = false;
    }
  }

  console.log("WebP support:", supportsWebP);
  new Phaser.Game(config);
}

window.addEventListener("DOMContentLoaded", () => {
  loadMemo();
  initGame();
});
