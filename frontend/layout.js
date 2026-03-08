// Star Office UI layout and layering configuration.
// Centralizing coordinates avoids scattered magic numbers across the scene setup.

const LAYOUT = {
  game: {
    width: 1280,
    height: 720
  },

  // Canonical area anchors used by movement/state rendering.
  areas: {
    door: { x: 640, y: 550 },
    workzone: { x: 320, y: 360 },
    research: { x: 320, y: 360 },
    incident_bay: { x: 1066, y: 180 },
    lounge: { x: 640, y: 360 }
  },

  furniture: {
    sofa: {
      x: 670,
      y: 144,
      origin: { x: 0, y: 0 },
      depth: 10
    },
    desk: {
      x: 218,
      y: 417,
      origin: { x: 0.5, y: 0.5 },
      depth: 1000
    },
    flower: {
      x: 310,
      y: 405,
      origin: { x: 0.5, y: 0.5 },
      depth: 1100
    },
    starWorking: {
      x: 217,
      y: 333,
      origin: { x: 0.5, y: 0.5 },
      depth: 900,
      scale: 1.32
    },
    plants: [
      { x: 565, y: 178, depth: 5 },
      { x: 230, y: 185, depth: 5 },
      { x: 977, y: 496, depth: 5 }
    ],
    poster: {
      x: 252,
      y: 66,
      depth: 4
    },
    coffeeMachine: {
      x: 659,
      y: 397,
      origin: { x: 0.5, y: 0.5 },
      depth: 99
    },
    serverroom: {
      x: 1021,
      y: 142,
      origin: { x: 0.5, y: 0.5 },
      depth: 2
    },
    errorBug: {
      x: 1007,
      y: 221,
      origin: { x: 0.5, y: 0.5 },
      depth: 50,
      scale: 0.9,
      pingPong: { leftX: 1007, rightX: 1111, speed: 0.6 }
    },
    syncAnim: {
      x: 1157,
      y: 592,
      origin: { x: 0.5, y: 0.5 },
      depth: 40
    },
    cat: {
      x: 94,
      y: 557,
      origin: { x: 0.5, y: 0.5 },
      depth: 2000
    }
  },

  plaque: {
    x: 640,
    y: 684,
    width: 420,
    height: 44
  },

  // Transparent assets stay PNG to avoid alpha artifacts.
  forcePng: {
    desk_v2: true
  },

  totalAssets: 15
};
