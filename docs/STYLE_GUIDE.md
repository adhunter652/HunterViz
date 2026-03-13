# App Style Guide

This document defines the visual and interaction style for the application. **The business landing page (`static/index.html`) is the canonical reference.** All new pages and components should follow these rules for a consistent look and feel.

---

## 1. Design tokens (CSS variables)

Use these CSS custom properties so colors and spacing can be updated in one place.

```css
:root {
  /* Backgrounds */
  --bg: #f8fafc;
  --surface: #ffffff;
  --header-bg: rgba(248, 250, 252, 0.9);

  /* Text */
  --text: #0f172a;
  --text-muted: #475569;

  /* Accent (primary actions, links, focus) */
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --accent-tint: rgba(59, 130, 246, 0.15);

  /* Borders & dividers */
  --border: rgba(15, 23, 42, 0.08);
}
```

| Token         | Hex / value              | Usage                                      |
|---------------|--------------------------|--------------------------------------------|
| `--bg`        | `#f8fafc`                | Page background                            |
| `--surface`   | `#ffffff`                | Cards, modals, raised panels               |
| `--text`      | `#0f172a`                | Primary body and heading text              |
| `--text-muted`| `#475569`                | Secondary text, captions, nav links        |
| `--accent`    | `#2563eb`                | Primary buttons, links, focus rings        |
| `--accent-hover` | `#1d4ed8`             | Hover state for accent elements            |
| `--accent-tint`  | `rgba(59,130,246,0.15)` | Subtle hover background for nav/text links |
| `--border`    | `rgba(15,23,42,0.08)`    | Input borders, card borders, dividers      |

---

## 2. Typography

### Font family

- **Primary:** `"DM Sans", system-ui, -apple-system, sans-serif`
- Load from Google Fonts (same as landing):
  ```html
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap" rel="stylesheet">
  ```

### Text styles

| Element        | Font size        | Weight | Color        | Notes                          |
|----------------|------------------|--------|-------------|--------------------------------|
| Page body      | 1rem (16px)      | 400    | `--text`    | `line-height: 1.5`             |
| Hero / page h1 | `clamp(2rem, 5vw, 3rem)` | 700 | `--text` | `letter-spacing: -0.03em`, `line-height: 1.15` |
| Section h2     | 1.5rem – 1.75rem | 600–700| `--text`    | Tighter letter-spacing optional|
| Subtitle / lead| 1.125rem         | 400    | `--text-muted` | Below hero or section title  |
| Labels         | 0.875rem         | 500    | `--text` or slightly muted | Form labels |
| Small / caption| 0.8125rem        | 400    | `--text-muted` | Footer, hints               |
| Nav links      | 0.875rem         | 500    | `--text-muted` (default)    | See Navigation below      |

---

## 3. Backgrounds and gradients

### Page background

- Default: solid `var(--bg)` (`#f8fafc`).

### Header (top bar)

- Gradient: **top to bottom**, from light blue into page background:
  - Start: `#bfdbfe`
  - End: `var(--bg)`
- Height: ~150px (or as needed for logo + nav).
- Content: flex, space-between, padding `1rem 1.5rem`.

```css
.header {
  background: linear-gradient(to bottom, #bfdbfe 0%, var(--bg) 100%);
  /* ... layout ... */
}
```

### Footer

- Gradient: **top to bottom**, from page background into slightly darker gray:
  - Start: `var(--bg)`
  - End: `#e2e8f0`
- Text: `--text-muted`, font-size `0.8125rem`, centered.

```css
.footer {
  background: linear-gradient(to bottom, var(--bg) 0%, #e2e8f0 100%);
  /* ... */
}
```

### Main content area

- Background: `var(--bg)` (no gradient).
- Use `--surface` for cards or form containers when content needs to sit on a solid panel.

---

## 4. Buttons

### Primary button (CTA, Sign up, Submit)

- **Background:** `var(--accent)`
- **Color:** `#fff`
- **Padding:** `0.875rem 1.75rem`
- **Border-radius:** `8px`
- **Font:** `1rem`, `font-weight: 600`
- **Border:** none
- **Cursor:** `pointer`

**Hover**

- Background: `var(--accent-hover)`
- Color: `#fff` (unchanged)

**Optional (for emphasis)**

- Slight gradient: `linear-gradient(180deg, #3b82f6 0%, #2563eb 100%)`
- Box-shadow: `0 2px 8px rgba(37, 99, 235, 0.4)`
- Hover: `filter: brightness(1.08);`
- Active: `transform: scale(0.99);`

**Disabled**

- `opacity: 0.7; cursor: not-allowed;`

### Secondary / ghost (e.g. Sign in, Log out)

- **Background:** transparent or very subtle (e.g. `--accent-tint` on hover only)
- **Color:** `--text-muted`
- **Padding:** `0.4rem 0.875rem` (compact) or `0.5rem 1rem`
- **Border-radius:** `6px`
- **Font:** `0.875rem`, `font-weight: 500`

**Hover**

- Color: `--text`
- Background: `var(--accent-tint)`

### Button-like links

- Use same padding, border-radius, and font weight as primary or secondary buttons so they match when used in nav or inline.

---

## 5. Links

### Inline text links

- **Color:** `var(--accent)` (or `#3b82f6`)
- **Text-decoration:** `none`
- **Hover:** `text-decoration: underline`

### Navigation links (no underline by default)

- Default: `color: var(--text-muted); text-decoration: none;`
- Hover: `color: var(--text); background: var(--accent-tint);`
- Padding: `0.4rem 0.875rem`, border-radius: `6px`, font-size: `0.875rem`, font-weight: `500`

---

## 6. Forms

### Container (card)

- **Background:** `var(--surface)` for light theme
- **Border:** `1px solid var(--border)`
- **Border-radius:** `10px` (or `8px` for smaller cards)
- **Padding:** `2rem` (or `2.5rem` for main forms)

### Labels

- **Display:** block
- **Margin-bottom:** `0.25rem` (or use gap in flex column)
- **Font:** `0.875rem`, `font-weight: 500`, color `--text` or slightly muted

### Inputs and textareas

- **Width:** `100%` within form
- **Padding:** `0.6rem 0.75rem` (inputs), `0.875rem 1rem` for larger touch targets
- **Font:** inherit, `1rem`
- **Color:** `--text`
- **Background:** `var(--surface)` or `var(--bg)` for a slight contrast
- **Border:** `1px solid var(--border)`
- **Border-radius:** `6px` (inputs) or `10px` (if matching card)
- **Placeholder:** `color: var(--text-muted)` or `#6b7a8c`

**Focus**

- **Outline:** `none`
- **Border-color:** accent, e.g. `rgba(59, 130, 246, 0.5)` or `var(--accent)`
- **Box-shadow:** `0 0 0 3px rgba(59, 130, 246, 0.15)` (focus ring)

**Transition (optional)**

- `transition: border-color 0.2s, box-shadow 0.2s;` for focus

### Textareas

- **Min-height:** `100px` (or as needed)
- **Resize:** `vertical` preferred

### Error state

- **Message text:** red, e.g. `#f87171` or `#ef4444`
- **Font-size:** `0.9rem`
- **Input error:** border color red (e.g. `#f87171`) when validation fails

### Submit row

- Margin above submit button: e.g. `margin-top: 0.5rem` or `1rem`
- Submit button: use **Primary button** styles, full width in narrow forms (`width: 100%`)

---

## 7. Interactive behavior summary

| Element           | Default                  | Hover                          | Focus (forms)        | Active (buttons)   |
|------------------|--------------------------|--------------------------------|----------------------|--------------------|
| Primary button   | Solid accent, white text | Darker accent, white text      | —                    | Slight scale down  |
| Secondary / nav  | Muted text, no bg        | Text color + accent-tint bg    | —                    | —                  |
| Link (inline)    | Accent, no underline     | Underline                      | —                    | —                  |
| Input / textarea | Border, bg               | —                              | Accent border + ring | —                  |
| Card (optional)  | Border                   | e.g. border accent tint        | —                    | —                  |

### Loading / disabled

- Buttons: when submitting, show "Sending…" or spinner; set `disabled` and use `opacity: 0.7; cursor: not-allowed;`.
- Forms: avoid multiple submissions; disable submit until request completes or on validation error.

---

## 8. Layout and spacing

- **Box-sizing:** `border-box` for all elements (`* { box-sizing: border-box; }`).
- **Body:** `min-height: 100vh`, flex column, `margin: 0`, font and colors from design tokens.
- **Main:** `flex: 1`, centered content, padding `2rem 1.5rem`.
- **Section width:** Hero/content max-width e.g. `720px` for readability; forms `360px`–`440px` single column.
- **Gaps:** Use `gap: 0.5rem`–`1.5rem` in flex/grid for consistent spacing between items.

---

## 9. Brand assets

- **Logo:** height ~32px in header; object-fit contain; border-radius `6px` optional.
- **Company name (image):** height ~24px in header; scale proportionally in footer (e.g. `height: 1em`).
- Keep aspect ratio; use same assets across landing, auth, and app pages for consistency.

**Logo image markup (canonical):**

```html
<img
    src="/assets/logo.png"
    alt=""
    class="logo-img"
    height="32"
    width="auto"
/>
```

- **On form pages (login, signup, subscribe, contact, etc.):** The logo (and brand link wrapping it) should be **centered** above the form. Use a flex container with `justify-content: center` (e.g. on the `.brand` element) so the logo is centered within the card.

---

## 10. Alignment with the landing page

When in doubt, match the business landing page:

- **Colors:** Use the same `:root` variables and gradient directions (header: blue → bg; footer: bg → gray).
- **Buttons:** Same primary (accent + hover) and secondary (muted + tint on hover) behavior.
- **Typography:** DM Sans, same scale (hero h1, subtitle, body, small).
- **Forms:** Same input height, radius, and focus ring so login, signup, contact, and subscribe feel like one app.

Pages that currently use a dark theme (e.g. auth, subscribe, contact) can be updated to this light theme for full consistency, or the guide can be extended later with an optional "dark variant" section if both are required.
