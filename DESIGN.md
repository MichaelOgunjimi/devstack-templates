---
version: "neuform-top-creators-featured"
name: "Aura - Curation Flow"
description: "Aura Curation Dashboard Section is designed for demonstrating application workflows and interface hierarchy. Key features include clear information density, modular panels, refined motion, premium editorial cards, and performant atmospheric WebGL."
colors:
  primary: "#7A9E7E"
  primary-strong: "#4A634D"
  secondary: "#E1E5DF"
  background: "#E1E5DF"
  background-soft: "#F4F6F2"
  surface-light: "#F4F6F2"
  surface-dark: "#181C19"
  surface-muted: "#E6EFE8"
  text-primary: "#111827"
  text-secondary: "#4B5563"
  text-dark: "#2C3B31"
  text-light: "#E1E5DF"
  border: "#2C3B31"
  border-subtle-light: "rgba(44, 59, 49, 0.10)"
  border-subtle-dark: "rgba(225, 229, 223, 0.10)"
typography:
  display-lg:
    fontFamily: "Playfair Display"
    fontSize: "40px"
    fontWeight: 500
    lineHeight: "1.04"
    letterSpacing: "-0.02em"
  display-md:
    fontFamily: "Playfair Display"
    fontSize: "32px"
    fontWeight: 500
    lineHeight: "1.08"
    letterSpacing: "-0.015em"
  body-md:
    fontFamily: "Geist"
    fontSize: "14px"
    fontWeight: 300
    lineHeight: "1.65"
    letterSpacing: "0"
  label-md:
    fontFamily: "Geist"
    fontSize: "11px"
    fontWeight: 400
    lineHeight: "1.2"
    letterSpacing: "0.14em"
spacing:
  base: "8px"
  gap: "16px"
  card-padding: "32px"
  card-gap: "24px"
  section-padding: "80px"
rounded:
  card: "8px"
  control: "8px"
  micro: "4px"
  pill: "9999px"
components:
  card:
    background: "Use light or dark surface tokens with soft inner contrast, subtle borders, and restrained shadow depth."
    radius: "Use the declared card radius token consistently across all cards."
    shadow: "Use layered low-opacity shadows rather than heavy drop shadows."
  button:
    background: "Use transparent controls for secondary actions and primary/accent colors only for main actions."
    radius: "Use control radius for icon buttons and pill radius only for explicit pill controls."
  chart:
    texture: "Use texture only on the active or highlighted bar. Keep inactive bars quiet and flat."
  canvas:
    role: "Ambient background only. Never compete with card content."
---

# Aura - Curation Flow

Source: Neuform Featured templates from top creators. Author: Meng To (@mengto). Views: 143; favorites: 31; remixes: 5.

Tags: dashboard, animated, webgl, threejs, bento, dither, charts, navigation.

## Overview

Aura is an editorial curation dashboard built around three horizontal mobile-first panels: artist profile, collection insights, and artwork detail. The visual language should feel calm, collectible, and museum-grade rather than generic SaaS. The interface should preserve the reference composition, compact information density, muted green palette, serif display typography, masked text reveals, and atmospheric WebGL backdrop.

The result should feel closer to an Apple product story card: quiet confidence, exact spacing, clear hierarchy, soft materials, no unnecessary decoration, and motion that supports comprehension.

## Composition

Use the attached HTML reference as the source of truth. Preserve the first-screen signal: three tall cards in a horizontal snap flow, each with a distinct role.

### Card 1: Artist Profile

Purpose: establish identity and historical context.

Visible hierarchy:

1. Artist dates
2. Artist name
3. Short biography
4. Signature works
5. Artwork list

Premium treatment:

- Keep the dark surface.
- Let the portrait sit as a cinematic background layer, not a raw image.
- Use a stronger bottom gradient so text feels embedded into the card.
- Keep artwork thumbnails small, editorial, and quiet.
- Make the list feel archival, not transactional.

Recommended structure:

```html
<main class="premium-card premium-card-dark">
  <div class="media-layer">
    <img />
    <div class="media-gradient"></div>
  </div>

  <header class="card-header"></header>

  <section class="card-content card-content-balanced">
    <div class="identity-block"></div>
    <div class="works-block"></div>
  </section>
</main>
```

### Card 2: Collection Insights

Purpose: provide operational context and analytics.

Visible hierarchy:

1. Curator identity
2. Collection Insights title
3. Engagement chart
4. Dashboard shortcuts

Premium treatment:

- Keep this as the clearest, brightest center card.
- Slightly increase its scale relative to side cards.
- Use the strongest information contrast here.
- Make chart bars feel precise and designed, not decorative.
- Use the active Q4 bar as the single accented data moment.

Recommended visual rule:

```css
.center-card {
  transform: scale(1.025);
  z-index: 2;
}
```

### Card 3: Artwork Detail

Purpose: create emotional focus around a selected work.

Visible hierarchy:

1. Artwork image
2. Metadata
3. Title
4. Primary media action
5. Description

Premium treatment:

- Keep the artwork image dominant but softened.
- Add a translucent lower information plane.
- Use blur and gradient only where they improve legibility.
- Keep the play button minimal and tactile.

Recommended treatment:

```css
.detail-info-plane {
  background: linear-gradient(
    to bottom,
    rgba(24, 28, 25, 0),
    rgba(24, 28, 25, 0.92) 36%,
    rgba(24, 28, 25, 1)
  );
  backdrop-filter: blur(10px);
}
```

## Colors

Anchor the palette in desaturated greens, bone whites, and deep charcoal green.

### Core roles

| Role | Token | Value | Usage |
|---|---:|---:|---|
| Primary | `primary` | `#7A9E7E` | Soft accent, hover states, data highlights |
| Strong Accent | `primary-strong` | `#4A634D` | Active data state, selected quarter, emphasized icon |
| Background | `background` | `#E1E5DF` | Page base |
| Light Surface | `surface-light` | `#F4F6F2` | Center dashboard card |
| Dark Surface | `surface-dark` | `#181C19` | Editorial image cards |
| Light Text | `text-light` | `#E1E5DF` | Dark card text |
| Dark Text | `text-dark` | `#2C3B31` | Light card text |

### Premium contrast rules

Use only three text opacity levels:

```css
--text-strong: 1;
--text-muted: 0.70;
--text-faint: 0.45;
```

Avoid arbitrary opacity values unless solving a specific contrast issue.

Use green as an interaction and emphasis color. Do not use it everywhere. Premium interfaces feel deliberate because accents are scarce.

## Typography

Use typography to create editorial hierarchy.

### Recommended stack

```css
:root {
  --font-display: "Playfair Display", Georgia, serif;
  --font-body: "Geist", Inter, system-ui, sans-serif;
}
```

### Display

Use `Playfair Display` for artist names, artwork names, and major card titles.

```css
.display-title {
  font-family: var(--font-display);
  font-size: 2rem;
  line-height: 1.06;
  letter-spacing: -0.018em;
  font-weight: 500;
}
```

### Body

Use `Geist` for descriptive copy, labels, controls, and dashboard metadata.

```css
.body-copy {
  font-family: var(--font-body);
  font-size: 0.875rem;
  line-height: 1.65;
  font-weight: 300;
}
```

### Labels

Use uppercase labels sparingly.

```css
.label {
  font-family: var(--font-body);
  font-size: 0.6875rem;
  line-height: 1.2;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
```

Do not overuse `tracking-widest`. Reserve it for metadata and section labels only.

## Layout

Use an 8px spacing system. Do not mix arbitrary values into the card rhythm.

### Spacing system

| Token | Value |
|---|---:|
| `space-1` | `4px` |
| `space-2` | `8px` |
| `space-3` | `12px` |
| `space-4` | `16px` |
| `space-6` | `24px` |
| `space-8` | `32px` |
| `space-12` | `48px` |

### Card shell

```css
.card-shell {
  width: 350px;
  height: 700px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
}
```

### Horizontal snap flow

```css
.snap-flow {
  display: flex;
  gap: 24px;
  width: max-content;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
}

.snap-card {
  scroll-snap-align: center;
  scroll-snap-stop: always;
}
```

### Scrollbar cleanup

```css
body {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

body::-webkit-scrollbar {
  display: none;
}
```

## Components

### Premium card material

Cards should feel like precise physical objects, not flat panels.

```css
.premium-card {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  box-shadow:
    0 1px 2px rgba(17, 24, 39, 0.06),
    0 18px 45px rgba(17, 24, 39, 0.10);
}

.premium-card::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.10);
}
```

### Dark editorial card

```css
.premium-card-dark {
  background:
    radial-gradient(circle at 50% 0%, rgba(122, 158, 126, 0.08), transparent 42%),
    #181C19;
  color: #E1E5DF;
}
```

### Light dashboard card

```css
.premium-card-light {
  background:
    linear-gradient(180deg, rgba(255,255,255,0.62), rgba(255,255,255,0.16)),
    #F4F6F2;
  color: #2C3B31;
}
```

### Icon buttons

```css
.icon-button {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: currentColor;
  opacity: 0.72;
  transition:
    opacity 180ms ease,
    transform 180ms ease,
    background-color 180ms ease;
}

.icon-button:hover {
  opacity: 1;
  transform: translateY(-1px);
  background: rgba(122, 158, 126, 0.10);
}

.icon-button:active {
  transform: translateY(0);
}
```

### Chart bars

Keep inactive bars flat. Use texture only on the highlighted data point.

```css
.chart-bar {
  border-radius: 4px;
  background: rgba(122, 158, 126, 0.12);
  border: 1px solid rgba(122, 158, 126, 0.24);
}

.chart-bar-active {
  position: relative;
  background:
    linear-gradient(
      45deg,
      transparent 25%,
      rgba(74, 99, 77, 0.14) 25%,
      rgba(74, 99, 77, 0.14) 50%,
      transparent 50%,
      transparent 75%,
      rgba(74, 99, 77, 0.14) 75%
    );
  background-size: 5px 5px;
  border-color: rgba(74, 99, 77, 0.46);
}
```

## Motion

Motion should feel expensive: subtle, fast enough to avoid drag, slow enough to read.

### Text reveal

Keep masked reveal, but avoid overusing it. Reveal only major headings and descriptive body copy.

```css
.reveal-word {
  display: inline-block;
  overflow: hidden;
  vertical-align: bottom;
}

.reveal-word-inner {
  display: inline-block;
  transform: translateY(100%);
  will-change: transform;
}
```

Recommended GSAP values:

```js
gsap.to(text.querySelectorAll(".reveal-word-inner"), {
  y: "0%",
  duration: 1.05,
  stagger: 0.035,
  ease: "power3.out",
  delay: 0.22
});
```

### Hover behavior

Use micro-lift only. Avoid obvious scaling except for the centered carousel card.

```css
.interactive-row {
  transition:
    transform 180ms ease,
    opacity 180ms ease,
    background-color 180ms ease;
}

.interactive-row:hover {
  transform: translateX(2px);
}
```

## WebGL & Effects

The canvas should behave like an atmospheric material layer. It should not draw attention away from the interface.

### Problems to avoid

- High-frequency animation.
- Excessive noise recalculated per frame at full strength.
- Sharp gradient movement.
- Running the shader when the tab is hidden.
- Rendering at uncontrolled device pixel ratio.
- Canvas updates when reduced motion is requested.

### Optimized visual direction

Use:

- Lower wave frequency.
- Slower time values.
- Reduced grain intensity.
- Clamped device pixel ratio.
- Pause on hidden tabs.
- Respect `prefers-reduced-motion`.
- Avoid unnecessary uniforms.
- Avoid expensive fragment logic.

### Optimized shader

```js
const initWebGLBackground = () => {
  const canvas = document.getElementById("webgl-bg");
  const gl = canvas?.getContext("webgl", {
    alpha: false,
    antialias: false,
    depth: false,
    stencil: false,
    preserveDrawingBuffer: false,
    powerPreference: "low-power"
  });

  if (!gl) return;

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let animationFrame = null;
  let running = true;

  const resize = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    const width = Math.floor(window.innerWidth * dpr);
    const height = Math.floor(window.innerHeight * dpr);

    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      gl.viewport(0, 0, width, height);
    }
  };

  window.addEventListener("resize", resize, { passive: true });
  resize();

  const vertexSource = `
    attribute vec2 position;
    varying vec2 vUv;

    void main() {
      vUv = position * 0.5 + 0.5;
      gl_Position = vec4(position, 0.0, 1.0);
    }
  `;

  const fragmentSource = `
    precision mediump float;

    varying vec2 vUv;
    uniform float uTime;
    uniform vec2 uResolution;

    float hash(vec2 p) {
      p = fract(p * vec2(123.34, 456.21));
      p += dot(p, p + 45.32);
      return fract(p.x * p.y);
    }

    void main() {
      vec2 uv = vUv;

      float waveX = sin((uv.x * 2.05) + (uTime * 0.18)) * 0.5 + 0.5;
      float waveY = cos((uv.y * 1.65) - (uTime * 0.12)) * 0.5 + 0.5;
      float field = smoothstep(0.12, 0.92, (waveX + waveY) * 0.5);

      vec3 warmBone = vec3(0.890, 0.902, 0.878);
      vec3 mutedSage = vec3(0.835, 0.851, 0.816);
      vec3 finalColor = mix(warmBone, mutedSage, field);

      float vignette = distance(uv, vec2(0.5));
      finalColor -= smoothstep(0.42, 0.88, vignette) * 0.035;

      float grain = hash((uv * uResolution) + floor(uTime * 12.0)) * 0.012;
      finalColor -= grain;

      gl_FragColor = vec4(finalColor, 1.0);
    }
  `;

  const compileShader = (type, source) => {
    const shader = gl.createShader(type);
    if (!shader) return null;

    gl.shaderSource(shader, source);
    gl.compileShader(shader);

    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.warn(gl.getShaderInfoLog(shader));
      gl.deleteShader(shader);
      return null;
    }

    return shader;
  };

  const vertexShader = compileShader(gl.VERTEX_SHADER, vertexSource);
  const fragmentShader = compileShader(gl.FRAGMENT_SHADER, fragmentSource);

  if (!vertexShader || !fragmentShader) return;

  const program = gl.createProgram();
  if (!program) return;

  gl.attachShader(program, vertexShader);
  gl.attachShader(program, fragmentShader);
  gl.linkProgram(program);

  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.warn(gl.getProgramInfoLog(program));
    return;
  }

  gl.useProgram(program);

  const vertices = new Float32Array([
    -1, -1,
     1, -1,
    -1,  1,
     1,  1
  ]);

  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

  const positionLocation = gl.getAttribLocation(program, "position");
  gl.enableVertexAttribArray(positionLocation);
  gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);

  const timeLocation = gl.getUniformLocation(program, "uTime");
  const resolutionLocation = gl.getUniformLocation(program, "uResolution");
  const startTime = performance.now();

  const render = now => {
    if (!running) return;

    const time = prefersReducedMotion ? 0 : (now - startTime) * 0.001;

    gl.uniform1f(timeLocation, time);
    gl.uniform2f(resolutionLocation, canvas.width, canvas.height);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    if (!prefersReducedMotion) {
      animationFrame = requestAnimationFrame(render);
    }
  };

  document.addEventListener("visibilitychange", () => {
    running = !document.hidden;

    if (running && !prefersReducedMotion) {
      animationFrame = requestAnimationFrame(render);
    } else if (animationFrame) {
      cancelAnimationFrame(animationFrame);
    }
  });

  render(performance.now());
};
```

### CSS support layer

```css
#webgl-bg {
  position: fixed;
  inset: 0;
  z-index: -10;
  width: 100%;
  height: 100%;
  pointer-events: none;
  transform: translateZ(0);
}
```

## Implementation Priorities

### Highest impact

1. Scale the center card slightly.
2. Reduce side-card visual dominance.
3. Normalize text opacity levels.
4. Convert arbitrary spacing to the 8px system.
5. Reduce WebGL motion speed and grain.
6. Use hatch texture only on the active chart bar.
7. Add stronger card material with layered subtle shadows.
8. Respect reduced motion and page visibility in WebGL.

### Suggested card visual balance

```css
.snap-card:not(.center-card) {
  opacity: 0.94;
}

.center-card {
  opacity: 1;
  transform: scale(1.025);
}
```

## Guardrails

- Do not flatten the source into a generic card grid.
- Do not replace the horizontal snap flow with a standard responsive SaaS section.
- Do not overuse green. Scarcity makes the accent feel premium.
- Do not use heavy shadows, large glow effects, or aggressive glassmorphism.
- Do not animate every element.
- Do not make the WebGL canvas the focal point.
- Preserve the first viewport signal, focal object, and compact visual density.
- Keep buttons, cards, thumbnails, and chart bars aligned to the same radius language.
- Preserve the editorial museum tone: quiet, tactile, precise, and atmospheric.
