import { mergePatch, effect, getPath } from "datastar";
import { createDebounce, createRAFThrottle } from "./throttle.js";
const SIZES = { handle: 8, corner: 12, tolerance: 2, throttle: 16 };
const COLORS = { hover: "rgba(0,123,255,.1)", drag: "rgba(0,123,255,.3)" };
const getCSSProp = (el, prop, fallback = "transparent") => getComputedStyle(el).getPropertyValue(`--split-${prop}`).trim() || fallback;
const getCSSPropPx = (el, prop, fallback = SIZES.handle) => Number.parseInt(getCSSProp(el, prop, `${fallback}px`)) || fallback;
const splits = /* @__PURE__ */ new Map();
const corners = /* @__PURE__ */ new Map();
function getGlobalConfig() {
  const cfg = window.__starhtml_split_config || {};
  return {
    signal: cfg.signal ?? "split",
    defaultMinSize: cfg.defaultMinSize ?? 10,
    responsive: cfg.responsive ?? false,
    responsiveBreakpoint: cfg.responsiveBreakpoint ?? 768
  };
}
function getSplitArgNames(signal = "split") {
  return [`${signal}_sizes`, `${signal}_direction`];
}
const rectCache = /* @__PURE__ */ new WeakMap();
function getCachedRect(element) {
  const now = Date.now();
  const cached = rectCache.get(element);
  if (cached && now - cached.timestamp < SIZES.throttle) {
    return cached.rect;
  }
  const rect = element.getBoundingClientRect();
  rectCache.set(element, { rect, timestamp: now });
  return rect;
}
function setCSS(el, signal, sizes) {
  for (const [i, size] of sizes.entries()) {
    el.style.setProperty(`--${signal}-panel-${i}`, `${size}%`);
  }
}
function stylePanels(panels, direction, signal, sizes, minSize) {
  const isH = direction === "horizontal";
  const handleSize = getCSSPropPx(panels[0] || document.documentElement, "handle-size");
  panels.forEach((panel, i) => {
    const handleShare = `${handleSize * (sizes[i] / 100)}px`;
    const sizeVar = `var(--${signal}-panel-${i})`;
    Object.assign(panel.style, {
      flex: isH ? `1 1 calc(${sizeVar} - ${handleShare})` : "none",
      height: isH ? "100%" : `calc(${sizeVar} - ${handleShare})`,
      width: isH ? "" : "100%",
      minWidth: isH ? `${minSize}%` : "",
      maxWidth: isH ? `${100 - minSize}%` : "",
      minHeight: !isH ? `${minSize}%` : "",
      maxHeight: !isH ? `${100 - minSize}%` : "",
      overflow: "auto",
      order: String(i * 2)
    });
    panel.dataset.splitPanel = String(i);
  });
}
function parseSplitValue(value) {
  if (!value?.includes(":")) return null;
  const [signal, direction, sizesStr] = value.split(":");
  if (!signal || !direction || !sizesStr) return null;
  if (direction !== "horizontal" && direction !== "vertical") return null;
  const sizes = sizesStr.split(",").map((s) => Number(s.trim())).filter((s) => s > 0);
  if (sizes.length === 0) return null;
  const total = sizes.reduce((a, b) => a + b, 0);
  return {
    signal,
    direction,
    sizes: sizes.map((s) => s / total * 100)
  };
}
function initializeElements(container, handle, direction, signal) {
  const isH = direction === "horizontal";
  const handleSize = getCSSPropPx(handle, "handle-size");
  Object.assign(container.style, {
    display: "flex",
    flexDirection: isH ? "row" : "column",
    position: "relative"
  });
  container.dataset.splitContainer = direction;
  container.dataset.splitSignal = signal;
  Object.assign(handle.style, {
    flexShrink: "0",
    position: "relative",
    zIndex: "10",
    touchAction: "none",
    userSelect: "none",
    order: "1",
    cursor: isH ? "col-resize" : "row-resize",
    background: getCSSProp(handle, "handle-color"),
    width: isH ? `${handleSize}px` : "",
    height: isH ? "" : `${handleSize}px`
  });
  handle.dataset.splitHandle = direction;
  handle.dataset.splitSignal = signal;
}
function getEventPosition(e) {
  if ("touches" in e) {
    return e.touches[0];
  }
  return e;
}
function createDragHandler(getPosition, onMove, onStart, onEnd) {
  let isDragging = false;
  let startPos = 0;
  return (e) => {
    e.preventDefault();
    const pos = getEventPosition(e);
    startPos = getPosition(pos);
    isDragging = true;
    onStart?.();
    const events = "touches" in e ? ["touchmove", "touchend"] : ["mousemove", "mouseup"];
    const handleDrag = (e2) => {
      if (!isDragging) return;
      const evt = e2;
      const pos2 = getEventPosition(evt);
      onMove(getPosition(pos2) - startPos);
    };
    const endDrag = () => {
      isDragging = false;
      onEnd?.();
      document.removeEventListener(events[0], handleDrag);
      document.removeEventListener(events[1], endDrag);
    };
    document.addEventListener(events[0], handleDrag, { passive: false });
    document.addEventListener(events[1], endDrag, { once: true });
  };
}
function calculateSplitSizes(delta, containerSize, startSizes, minSize) {
  if (startSizes.length !== 2) return startSizes;
  const size1 = Math.max(
    minSize,
    Math.min(100 - minSize, startSizes[0] + delta / containerSize * 100)
  );
  return [size1, 100 - size1];
}
function setupDragHandling(state, _ctx) {
  const { handle, container, signal, minSize } = state;
  let startSizes = [];
  let containerSize = 0;
  let isDragging = false;
  const updateSizes = createRAFThrottle((delta) => {
    const newSizes = calculateSplitSizes(delta, containerSize, startSizes, minSize);
    if (newSizes === startSizes) return;
    state.sizes = newSizes;
    setCSS(container, signal, newSizes);
    mergePatch({ [`${signal}_sizes`]: newSizes });
  });
  const startDrag = createDragHandler(
    (pos) => state.direction === "horizontal" ? pos.clientX : pos.clientY,
    (delta) => updateSizes(delta),
    () => {
      const rect = getCachedRect(container);
      containerSize = state.direction === "horizontal" ? rect.width : rect.height;
      startSizes = [...state.sizes];
      isDragging = true;
      Object.assign(handle.style, {
        opacity: "0.8",
        background: getCSSProp(handle, "handle-active-color", COLORS.drag)
      });
    },
    () => {
      isDragging = false;
      Object.assign(handle.style, {
        opacity: "",
        background: getCSSProp(handle, "handle-color")
      });
    }
  );
  const handleHover = (e) => {
    if (!isDragging) {
      handle.style.background = e.type === "mouseenter" ? getCSSProp(handle, "handle-hover-color", COLORS.hover) : getCSSProp(handle, "handle-color");
    }
  };
  handle.addEventListener("mouseenter", handleHover);
  handle.addEventListener("mouseleave", handleHover);
  handle.addEventListener("mousedown", startDrag);
  handle.addEventListener("touchstart", startDrag, { passive: false });
}
function setupResponsiveHandling(state, config, _ctx) {
  if (!config.responsive) return null;
  const handleResize = createDebounce(() => {
    const newDirection = window.innerWidth <= config.responsiveBreakpoint ? "vertical" : "horizontal";
    if (newDirection !== state.direction) {
      state.direction = newDirection;
      const { container, handle, signal, panels, sizes, minSize } = state;
      handle.setAttribute("data-split", `${signal}:${newDirection}:${sizes.join(",")}`);
      initializeElements(container, handle, newDirection, signal);
      stylePanels(panels, newDirection, signal, sizes, minSize);
      mergePatch({ [`${signal}_direction`]: newDirection });
    }
  }, 150);
  window.addEventListener("resize", handleResize);
  return () => window.removeEventListener("resize", handleResize);
}
function detectAndCreateCornerHandles(ctx) {
  const allSplits = [...splits.values()];
  const hSplits = allSplits.filter((s) => s.direction === "horizontal");
  const vSplits = allSplits.filter((s) => s.direction === "vertical");
  if (!hSplits.length || !vSplits.length) return false;
  for (const h of hSplits) {
    for (const v of vSplits) {
      const key = `${h.signal}-${v.signal}`;
      if (corners.has(key)) continue;
      const hRect = getCachedRect(h.handle);
      const vRect = getCachedRect(v.handle);
      const overlaps = hRect.left <= vRect.right + SIZES.tolerance && hRect.right >= vRect.left - SIZES.tolerance && hRect.top <= vRect.bottom + SIZES.tolerance && hRect.bottom >= vRect.top - SIZES.tolerance;
      if (overlaps) {
        createCornerHandle(h, v, hRect, vRect);
      }
    }
  }
  return hSplits.length > 0 && vSplits.length > 0;
}
function createCornerHandle(h, v, hRect, vRect, ctx) {
  const corner = document.createElement("div");
  const key = `${h.signal}-${v.signal}`;
  corner.className = "split-corner-handle";
  corner.dataset.splitCorner = key;
  Object.assign(corner.style, {
    position: "fixed",
    width: `${SIZES.corner}px`,
    height: `${SIZES.corner}px`,
    zIndex: "1000",
    cursor: "move",
    background: "transparent"
  });
  updateCornerPosition(corner, hRect, vRect);
  document.body.appendChild(corner);
  const cornerHandle = { element: corner, horizontalSplit: h, verticalSplit: v };
  corners.set(key, cornerHandle);
  setupCornerDragHandling(cornerHandle);
  effect(() => {
    const hSizes = getPath(`${h.signal}_sizes`);
    const vSizes = getPath(`${v.signal}_sizes`);
    if (hSizes || vSizes) {
      requestAnimationFrame(() => {
        updateCornerPosition(corner, getCachedRect(h.handle), getCachedRect(v.handle));
      });
    }
  });
}
function updateCornerPosition(element, hRect, vRect) {
  element.style.left = `${Math.max(hRect.right, vRect.left) - SIZES.corner / 2}px`;
  element.style.top = `${vRect.top + vRect.height / 2 - SIZES.corner / 2}px`;
}
function setupCornerDragHandling(corner, _ctx) {
  const { element, horizontalSplit: h, verticalSplit: v } = corner;
  let startPos = { x: 0, y: 0 };
  let startSizes = { h: [...h.sizes], v: [...v.sizes] };
  let containerSizes = { h: 0, v: 0 };
  let isDragging = false;
  const updateSplit = (split, delta, containerSize, startSize) => {
    const sizes = calculateSplitSizes(delta, containerSize, startSize, split.minSize);
    split.sizes = sizes;
    setCSS(split.container, split.signal, sizes);
    mergePatch({ [`${split.signal}_sizes`]: sizes });
    return sizes;
  };
  const updateBothSplits = createRAFThrottle((deltaX, deltaY) => {
    if (!isDragging) return;
    updateSplit(h, deltaX, containerSizes.h, startSizes.h);
    updateSplit(v, deltaY, containerSizes.v, startSizes.v);
    requestAnimationFrame(() => {
      updateCornerPosition(element, getCachedRect(h.handle), getCachedRect(v.handle));
    });
  });
  const startDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const pos = getEventPosition(e);
    startPos = { x: pos.clientX, y: pos.clientY };
    startSizes = { h: [...h.sizes], v: [...v.sizes] };
    const hRect = getCachedRect(h.container);
    const vRect = getCachedRect(v.container);
    containerSizes = { h: hRect.width, v: vRect.height };
    isDragging = true;
    const events = "touches" in e ? ["touchmove", "touchend"] : ["mousemove", "mouseup"];
    const handleDrag = (e2) => {
      if (!isDragging) return;
      const evt = e2;
      const pos2 = getEventPosition(evt);
      updateBothSplits(pos2.clientX - startPos.x, pos2.clientY - startPos.y);
    };
    const endDrag = () => {
      isDragging = false;
      document.removeEventListener(events[0], handleDrag);
      document.removeEventListener(events[1], endDrag);
    };
    document.addEventListener(events[0], handleDrag, { passive: false });
    document.addEventListener(events[1], endDrag, { once: true });
  };
  element.addEventListener("mousedown", startDrag);
  element.addEventListener("touchstart", startDrag, { passive: false });
}
const splitAttributePlugin = {
  name: "split",
  requirement: { key: "allowed", value: "allowed" },
  argNames: getSplitArgNames(),
  apply(ctx) {
    const { el: handle, value } = ctx;
    const config = parseSplitValue(value ?? "");
    if (!config || handle.dataset.splitInit === "true") return;
    const { signal, direction, sizes } = config;
    const globalConfig = getGlobalConfig();
    const currentDirection = globalConfig.responsive && window.innerWidth <= globalConfig.responsiveBreakpoint ? "vertical" : direction;
    const container = handle.parentElement;
    if (!container) return;
    const panels = Array.from(container.children).filter(
      (c) => c !== handle && !c.dataset.split?.includes(":")
    );
    if (panels.length !== sizes.length) return;
    handle.dataset.splitInit = "true";
    initializeElements(container, handle, currentDirection, signal);
    setCSS(container, signal, sizes);
    stylePanels(panels, currentDirection, signal, sizes, globalConfig.defaultMinSize);
    const state = {
      container,
      handle,
      signal,
      direction: currentDirection,
      sizes,
      panels,
      minSize: globalConfig.defaultMinSize
    };
    splits.set(handle, state);
    mergePatch({
      [`${signal}_sizes`]: sizes,
      [`${signal}_direction`]: currentDirection
    });
    setupDragHandling(state);
    const resizeCleanup = setupResponsiveHandling(state, globalConfig);
    let cornerCleanup = null;
    const hasCorners = detectAndCreateCornerHandles();
    if (hasCorners) {
      const updateCornerPositions = createDebounce(() => {
        for (const { horizontalSplit: h, verticalSplit: v, element } of corners.values()) {
          updateCornerPosition(element, getCachedRect(h.handle), getCachedRect(v.handle));
        }
      }, 50);
      window.addEventListener("resize", updateCornerPositions);
      cornerCleanup = () => window.removeEventListener("resize", updateCornerPositions);
    }
    const effectCleanup = effect(() => {
      const currentSizes = getPath(`${signal}_sizes`);
      if (currentSizes?.length && !arraysEqual(currentSizes, state.sizes)) {
        state.sizes = currentSizes;
        setCSS(container, signal, currentSizes);
        stylePanels(panels, state.direction, signal, currentSizes, state.minSize);
      }
    });
    return () => {
      effectCleanup();
      resizeCleanup?.();
      cornerCleanup?.();
      splits.delete(handle);
      for (const [key, c] of corners.entries()) {
        if (c.horizontalSplit === state || c.verticalSplit === state) {
          c.element.remove();
          corners.delete(key);
        }
      }
      handle.dataset.splitInit = "false";
    };
  }
};
function arraysEqual(a, b, threshold = 0.01) {
  return a.length === b.length && a.every((val, i) => Math.abs(val - b[i]) < threshold);
}
const splitPlugin = {
  ...splitAttributePlugin,
  setConfig(config) {
    window.__starhtml_split_config = { ...getGlobalConfig(), ...config };
    const signal = config?.signal ? String(config.signal) : "split";
    this.argNames = getSplitArgNames(signal);
  }
};
var split_default = splitPlugin;
export {
  split_default as default
};
