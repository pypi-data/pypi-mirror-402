import { mergePatch } from "datastar";
function getCanvasArgNames(signal = "canvas") {
  return [
    `${signal}_pan_x`,
    `${signal}_pan_y`,
    `${signal}_zoom`,
    `${signal}_reset_view`,
    `${signal}_zoom_in`,
    `${signal}_zoom_out`,
    `${signal}_context_menu_x`,
    `${signal}_context_menu_y`,
    `${signal}_context_menu_screen_x`,
    `${signal}_context_menu_screen_y`
  ];
}
function parseConfig(config) {
  return {
    signal: config?.signal || "canvas",
    enablePan: config?.enablePan !== false,
    enableZoom: config?.enableZoom !== false,
    minZoom: config?.minZoom || 0.01,
    maxZoom: config?.maxZoom || 100,
    touchEnabled: config?.touchEnabled !== false,
    contextMenuEnabled: config?.contextMenuEnabled !== false,
    spacebarPan: config?.spacebarPan !== false,
    middleClickPan: config?.middleClickPan !== false,
    backgroundColor: config?.backgroundColor || "#f8f9fa",
    enableGrid: config?.enableGrid !== false,
    gridSize: config?.gridSize || 100,
    gridColor: config?.gridColor || "#e0e0e0",
    minorGridSize: config?.minorGridSize || 20,
    minorGridColor: config?.minorGridColor || "#f0f0f0"
  };
}
const ZOOM_FACTOR = 1.2;
const WHEEL_ZOOM_IN = 1.05;
const WHEEL_ZOOM_OUT = 0.95;
class CanvasController {
  constructor(ctx, config) {
    this.ctx = ctx;
    this.camera = { x: 0, y: 0, z: 1 };
    this.viewport = null;
    this.container = null;
    this.lastSent = {};
    this.gestureState = {
      pointers: /* @__PURE__ */ new Map(),
      isGesturing: false,
      mode: "none"
    };
    this.isPanning = false;
    this.lastPanPoint = null;
    this.isSpacePressed = false;
    this.rafId = null;
    this.lastViewportWidth = 0;
    this.lastViewportHeight = 0;
    this.resizeObserver = null;
    this.boundHandlePointerDown = this.handlePointerDown.bind(this);
    this.boundHandleWheel = this.handleWheel.bind(this);
    this.boundHandleKeyDown = this.handleKeyDown.bind(this);
    this.boundHandleKeyUp = this.handleKeyUp.bind(this);
    this.boundHandleContextMenu = this.handleContextMenu.bind(this);
    this.boundHandlePointerMove = this.handlePointerMove.bind(this);
    this.boundHandlePointerUp = this.handlePointerUp.bind(this);
    this.config = config;
    this.setupEventListeners();
    this.initializeDOMElements();
    this.registerInGlobalRegistry();
  }
  registerInGlobalRegistry() {
    controllerRegistry[this.config.signal] = this;
  }
  setContext(ctx) {
    this.ctx = ctx;
  }
  setupEventListeners() {
    document.addEventListener("pointerdown", this.boundHandlePointerDown);
    document.addEventListener("wheel", this.boundHandleWheel, { passive: false });
    if (this.config.spacebarPan) {
      document.addEventListener("keydown", this.boundHandleKeyDown);
      document.addEventListener("keyup", this.boundHandleKeyUp);
    }
    if (this.config.contextMenuEnabled) {
      document.addEventListener("contextmenu", this.boundHandleContextMenu);
    }
  }
  initializeDOMElements() {
    requestAnimationFrame(() => {
      this.viewport = document.querySelector("[data-canvas-viewport]");
      this.container = document.querySelector("[data-canvas-container]");
      if (this.viewport) {
        this.setupViewportStyles();
        this.setupResizeObserver();
        this.centerCanvas();
      }
      this.scheduleRender();
    });
  }
  centerCanvas() {
    if (!this.viewport) return;
    const rect = this.viewport.getBoundingClientRect();
    const viewportWidth = rect.width;
    const viewportHeight = rect.height;
    this.camera.x = viewportWidth / 2 / this.camera.z;
    this.camera.y = viewportHeight / 2 / this.camera.z;
  }
  setupResizeObserver() {
    if (!this.viewport) return;
    const rect = this.viewport.getBoundingClientRect();
    this.lastViewportWidth = rect.width;
    this.lastViewportHeight = rect.height;
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        this.handleViewportResize(entry.contentRect);
      }
    });
    resizeObserver.observe(this.viewport);
    this.resizeObserver = resizeObserver;
  }
  handleViewportResize(rect) {
    const newWidth = rect.width;
    const newHeight = rect.height;
    if (newWidth === this.lastViewportWidth && newHeight === this.lastViewportHeight) {
      return;
    }
    if (newWidth === 0 || newHeight === 0) {
      return;
    }
    const oldCenterX = this.lastViewportWidth / 2;
    const oldCenterY = this.lastViewportHeight / 2;
    const worldCenterX = oldCenterX / this.camera.z - this.camera.x;
    const worldCenterY = oldCenterY / this.camera.z - this.camera.y;
    const newCenterX = newWidth / 2;
    const newCenterY = newHeight / 2;
    this.camera.x = newCenterX / this.camera.z - worldCenterX;
    this.camera.y = newCenterY / this.camera.z - worldCenterY;
    this.lastViewportWidth = newWidth;
    this.lastViewportHeight = newHeight;
    this.scheduleRender();
  }
  setupViewportStyles() {
    if (!this.viewport) return;
    Object.assign(this.viewport.style, {
      userSelect: "none",
      webkitUserSelect: "none",
      touchAction: "none",
      cursor: "grab",
      willChange: "transform",
      backgroundColor: this.config.backgroundColor,
      ...window.devicePixelRatio > 1 && { imageRendering: "pixelated" }
    });
    if (this.config.enableGrid) {
      this.applyGridStyles();
    }
  }
  applyGridStyles() {
    if (!this.viewport) return;
    const gridSize = this.config.gridSize || 100;
    const gridColor = this.config.gridColor || "rgba(0,0,0,0.1)";
    const minorSize = this.config.minorGridSize || 20;
    const minorColor = this.config.minorGridColor || "rgba(0,0,0,0.05)";
    const bgImage = [
      `linear-gradient(${gridColor} 1px, transparent 1px)`,
      `linear-gradient(90deg, ${gridColor} 1px, transparent 1px)`,
      `linear-gradient(${minorColor} 1px, transparent 1px)`,
      `linear-gradient(90deg, ${minorColor} 1px, transparent 1px)`
    ].join(",");
    this.viewport.style.backgroundImage = bgImage;
    this.viewport.style.backgroundSize = [
      `${gridSize}px ${gridSize}px`,
      `${gridSize}px ${gridSize}px`,
      `${minorSize}px ${minorSize}px`,
      `${minorSize}px ${minorSize}px`
    ].join(",");
    this.updateGridPosition();
  }
  updateGridPosition() {
    if (!this.viewport || !this.config.enableGrid) return;
    const gridSize = this.config.gridSize || 100;
    const minorSize = this.config.minorGridSize || 20;
    const scaledGridSize = gridSize * this.camera.z;
    const scaledMinorSize = minorSize * this.camera.z;
    const majorOffsetX = this.camera.x * this.camera.z % scaledGridSize;
    const majorOffsetY = this.camera.y * this.camera.z % scaledGridSize;
    const minorOffsetX = this.camera.x * this.camera.z % scaledMinorSize;
    const minorOffsetY = this.camera.y * this.camera.z % scaledMinorSize;
    this.viewport.style.backgroundPosition = [
      `${majorOffsetX}px ${majorOffsetY}px`,
      `${majorOffsetX}px ${majorOffsetY}px`,
      `${minorOffsetX}px ${minorOffsetY}px`,
      `${minorOffsetX}px ${minorOffsetY}px`
    ].join(",");
    this.viewport.style.backgroundSize = [
      `${scaledGridSize}px ${scaledGridSize}px`,
      `${scaledGridSize}px ${scaledGridSize}px`,
      `${scaledMinorSize}px ${scaledMinorSize}px`,
      `${scaledMinorSize}px ${scaledMinorSize}px`
    ].join(",");
  }
  handlePointerDown(evt) {
    const target = evt.target;
    const draggableElement = target.closest("[data-drag]");
    if (draggableElement) {
      return;
    }
    const viewport = target.closest("[data-canvas-viewport]");
    if (!viewport || !this.config.enablePan) return;
    this.viewport = viewport;
    this.gestureState.pointers.set(evt.pointerId, evt);
    const pointerCount = this.gestureState.pointers.size;
    if (pointerCount === 1) {
      this.handleSinglePointerDown(evt);
    } else if (pointerCount === 2) {
      this.handleMultiTouchStart();
    }
  }
  handleSinglePointerDown(evt) {
    const isLeftClick = evt.button === 0;
    const isMiddleClick = evt.button === 1 && this.config.middleClickPan;
    const isSpacePan = this.isSpacePressed && isLeftClick;
    if (!isLeftClick && !isMiddleClick && !isSpacePan) return;
    evt.preventDefault();
    this.startPanning(evt);
  }
  handleMultiTouchStart() {
    if (!this.config.touchEnabled) return;
    const pointers = Array.from(this.gestureState.pointers.values());
    if (pointers.length !== 2) return;
    this.gestureState.mode = "pinch";
    this.gestureState.isGesturing = true;
    this.gestureState.initialDistance = this.getDistance(pointers[0], pointers[1]);
    this.gestureState.initialCenter = this.getCenter(pointers[0], pointers[1]);
    this.gestureState.initialCamera = { ...this.camera };
    if (this.viewport) {
      const rect = this.viewport.getBoundingClientRect();
      const screenPoint = {
        x: this.gestureState.initialCenter.x - rect.left,
        y: this.gestureState.initialCenter.y - rect.top
      };
      this.gestureState.fixedWorldPoint = this.screenToCanvas(screenPoint);
    }
    this.stopPanning();
  }
  startPanning(evt) {
    this.isPanning = true;
    this.gestureState.mode = "pan";
    this.lastPanPoint = { x: evt.clientX, y: evt.clientY };
    if (this.viewport) {
      this.viewport.style.cursor = "grabbing";
    }
    document.addEventListener("pointermove", this.boundHandlePointerMove);
    document.addEventListener("pointerup", this.boundHandlePointerUp);
    document.addEventListener("pointercancel", this.boundHandlePointerUp);
  }
  stopPanning() {
    this.isPanning = false;
    this.lastPanPoint = null;
    if (this.viewport) {
      this.viewport.style.cursor = "grab";
    }
    document.removeEventListener("pointermove", this.boundHandlePointerMove);
    document.removeEventListener("pointerup", this.boundHandlePointerUp);
    document.removeEventListener("pointercancel", this.boundHandlePointerUp);
  }
  handlePointerMove(evt) {
    this.gestureState.pointers.set(evt.pointerId, evt);
    if (this.gestureState.mode === "pan" && this.isPanning) {
      this.handlePanMove(evt);
    } else if (this.gestureState.mode === "pinch" && this.gestureState.pointers.size === 2) {
      this.handlePinchMove();
    }
  }
  handlePanMove(evt) {
    if (!this.lastPanPoint) return;
    const deltaX = evt.clientX - this.lastPanPoint.x;
    const deltaY = evt.clientY - this.lastPanPoint.y;
    this.camera.x += deltaX / this.camera.z;
    this.camera.y += deltaY / this.camera.z;
    this.lastPanPoint = { x: evt.clientX, y: evt.clientY };
    this.scheduleRender();
  }
  handlePinchMove() {
    const pointers = Array.from(this.gestureState.pointers.values());
    if (pointers.length !== 2) return;
    const currentDistance = this.getDistance(pointers[0], pointers[1]);
    const currentCenter = this.getCenter(pointers[0], pointers[1]);
    if (this.gestureState.initialDistance && this.gestureState.initialCamera && this.viewport) {
      const scaleFactor = currentDistance / this.gestureState.initialDistance;
      const targetZoom = this.clampZoom(this.gestureState.initialCamera.z * scaleFactor);
      const rect = this.viewport.getBoundingClientRect();
      const pinchScreenX = currentCenter.x - rect.left;
      const pinchScreenY = currentCenter.y - rect.top;
      if (targetZoom !== this.camera.z) {
        this.zoomAtPoint(pinchScreenX, pinchScreenY, targetZoom / this.camera.z);
      }
    }
  }
  handlePointerUp(evt) {
    this.gestureState.pointers.delete(evt.pointerId);
    if (this.gestureState.pointers.size === 0) {
      this.gestureState.mode = "none";
      this.gestureState.isGesturing = false;
      this.stopPanning();
    } else if (this.gestureState.pointers.size === 1 && this.gestureState.mode === "pinch") {
      const remainingPointer = Array.from(this.gestureState.pointers.values())[0];
      this.startPanning(remainingPointer);
    }
  }
  handleWheel(evt) {
    const target = evt.target;
    const viewport = target.closest("[data-canvas-viewport]");
    if (!viewport || !this.config.enableZoom) return;
    evt.preventDefault();
    const rect = viewport.getBoundingClientRect();
    const mouseX = evt.clientX - rect.left;
    const mouseY = evt.clientY - rect.top;
    const zoomFactor = evt.deltaY > 0 ? WHEEL_ZOOM_OUT : WHEEL_ZOOM_IN;
    this.zoomAtPoint(mouseX, mouseY, zoomFactor);
  }
  handleKeyDown(evt) {
    if (evt.code === "Space" && this.config.spacebarPan) {
      evt.preventDefault();
      if (!this.isSpacePressed) {
        this.isSpacePressed = true;
        if (this.viewport) {
          this.viewport.style.cursor = "grab";
        }
      }
    }
    if ((evt.ctrlKey || evt.metaKey) && this.config.enableZoom) {
      const zoomActions = {
        "=": () => this.zoomAtCenter(ZOOM_FACTOR),
        "+": () => this.zoomAtCenter(ZOOM_FACTOR),
        "-": () => this.zoomAtCenter(1 / ZOOM_FACTOR),
        "0": () => this.resetView()
      };
      const action = zoomActions[evt.key];
      if (action) {
        action();
        evt.preventDefault();
      }
    }
  }
  handleKeyUp(evt) {
    if (evt.code === "Space" && this.config.spacebarPan) {
      evt.preventDefault();
      this.isSpacePressed = false;
      if (this.viewport && !this.isPanning) {
        this.viewport.style.cursor = "grab";
      }
    }
  }
  handleContextMenu(evt) {
    const target = evt.target;
    const viewport = target.closest("[data-canvas-viewport]");
    if (!viewport) return;
    evt.preventDefault();
    const rect = viewport.getBoundingClientRect();
    const canvasPoint = this.screenToCanvas({
      x: evt.clientX - rect.left,
      y: evt.clientY - rect.top
    });
    const updates = {
      [`${this.config.signal}_context_menu_x`]: canvasPoint.x,
      [`${this.config.signal}_context_menu_y`]: canvasPoint.y,
      [`${this.config.signal}_context_menu_screen_x`]: evt.clientX,
      [`${this.config.signal}_context_menu_screen_y`]: evt.clientY
    };
    mergePatch(updates);
  }
  clampZoom(zoom) {
    return Math.max(this.config.minZoom, Math.min(this.config.maxZoom, zoom));
  }
  zoomAtPoint(screenX, screenY, zoomFactor) {
    const oldZoom = this.camera.z;
    const newZoom = this.clampZoom(oldZoom * zoomFactor);
    if (newZoom !== oldZoom) {
      const worldX = screenX / oldZoom - this.camera.x;
      const worldY = screenY / oldZoom - this.camera.y;
      this.camera.z = newZoom;
      this.camera.x = screenX / newZoom - worldX;
      this.camera.y = screenY / newZoom - worldY;
      this.scheduleRender();
    }
  }
  zoomAtCenter(zoomFactor) {
    if (!this.viewport) return;
    const rect = this.viewport.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    this.zoomAtPoint(centerX, centerY, zoomFactor);
  }
  resetView() {
    this.camera.z = 1;
    this.centerCanvas();
    this.scheduleRender();
  }
  zoomIn() {
    this.zoomAtCenter(ZOOM_FACTOR);
  }
  zoomOut() {
    this.zoomAtCenter(1 / ZOOM_FACTOR);
  }
  screenToCanvas(point) {
    return {
      x: point.x / this.camera.z - this.camera.x,
      y: point.y / this.camera.z - this.camera.y
    };
  }
  canvasToScreen(point) {
    return {
      x: (point.x + this.camera.x) * this.camera.z,
      y: (point.y + this.camera.y) * this.camera.z
    };
  }
  getDistance(pointer1, pointer2) {
    return Math.sqrt(
      (pointer2.clientX - pointer1.clientX) ** 2 + (pointer2.clientY - pointer1.clientY) ** 2
    );
  }
  getCenter(pointer1, pointer2) {
    return {
      x: (pointer1.clientX + pointer2.clientX) / 2,
      y: (pointer1.clientY + pointer2.clientY) / 2
    };
  }
  scheduleRender() {
    if (this.rafId !== null) return;
    this.rafId = requestAnimationFrame(() => {
      this.rafId = null;
      this.updateTransform();
      this.updateGridPosition();
      this.updateSignals();
    });
  }
  updateTransform() {
    if (!this.container) return;
    const transform = `translate(${this.camera.x * this.camera.z}px, ${this.camera.y * this.camera.z}px) scale(${this.camera.z})`;
    this.container.style.transform = transform;
    this.container.style.transformOrigin = "0 0";
  }
  updateSignals() {
    const updates = {
      [`${this.config.signal}_pan_x`]: this.camera.x,
      [`${this.config.signal}_pan_y`]: this.camera.y,
      [`${this.config.signal}_zoom`]: this.camera.z
    };
    const patch = {};
    for (const k in updates) {
      if (this.lastSent[k] !== updates[k]) patch[k] = updates[k];
    }
    if (Object.keys(patch).length === 0) return;
    mergePatch(patch);
    this.ctx.rx?.(this.camera.x, this.camera.y, this.camera.z, this.isPanning);
    Object.assign(this.lastSent, patch);
  }
  destroy() {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
    }
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    controllerRegistry[this.config.signal] = null;
    document.removeEventListener("pointerdown", this.boundHandlePointerDown);
    document.removeEventListener("wheel", this.boundHandleWheel);
    document.removeEventListener("keydown", this.boundHandleKeyDown);
    document.removeEventListener("keyup", this.boundHandleKeyUp);
    document.removeEventListener("contextmenu", this.boundHandleContextMenu);
    this.stopPanning();
  }
}
const canvasAttributePlugin = {
  name: "canvas",
  requirement: { key: "allowed", value: "allowed" },
  apply(ctx) {
    const globalConfig = window.__starhtml_canvas_config;
    const config = parseConfig(globalConfig);
    const controller = new CanvasController(ctx, config);
    return () => {
      controller.destroy();
    };
  }
};
const controllerRegistry = {};
function registerCanvasActions(signal) {
  const actionsKey = `__${signal}`;
  if (window[actionsKey]) return;
  window[actionsKey] = {
    resetView: () => controllerRegistry[signal]?.resetView(),
    zoomIn: () => controllerRegistry[signal]?.zoomIn(),
    zoomOut: () => controllerRegistry[signal]?.zoomOut()
  };
}
const canvasPlugin = {
  ...canvasAttributePlugin,
  argNames: [],
  setConfig(config) {
    window.__starhtml_canvas_config = config;
    const signal = config?.signal ? String(config.signal) : "canvas";
    this.argNames = getCanvasArgNames(signal);
    registerCanvasActions(signal);
  }
};
var canvas_default = canvasPlugin;
export {
  canvas_default as default
};
