# `web/design-system`

The shared component library. Published to Harbor as an npm/OCI package and **version-pinned to
the platform release**.

Every module's custom micro-frontend must consume it. This is the only thing that makes twenty
independently-developed screens look like one product.

## Contents

```
src/
  tokens/       colour, spacing, typography, radii — CSS custom properties
  primitives/   Button, Input, Select, Badge, Table, Tabs, Dialog, Toast
  patterns/     PageHeader, FilterBar, EmptyState, ErrorState, Pagination
  theme/        light/dark, high contrast, customer white-labelling hooks
```

## Example — tokens, not hardcoded values

```css
/* tokens/colour.css
   Modules reference semantic names, never raw values. That is what lets a customer
   white-label the platform, and what lets us ship a dark theme, without touching a
   single module's code. A hex value inside a module is a bug. */
:root {
  --bss-color-surface: #ffffff;
  --bss-color-text: #111418;
  --bss-color-accent: #1c6fd0;

  --bss-color-status-active: #107c41;
  --bss-color-status-warning: #9a6700;
  --bss-color-status-neutral: #5c636a;
}

:root[data-theme="dark"] {
  --bss-color-surface: #14171a;
  --bss-color-text: #f2f4f6;
  --bss-color-accent: #4da6ff;
}
```

```tsx
// primitives/Badge.tsx
//
// The Shell renders enum fields marked x-ui.widget=badge through this component, mapping
// enumColors from the module's metadata onto semantic tokens. A module declares MEANING
// ("warning"); the design system decides appearance.
export function Badge({ tone = "neutral", children }: BadgeProps) {
  return <span className={`bss-badge bss-badge--${tone}`}>{children}</span>;
}
```

## Versioning risk

This package can become the bottleneck that blocks every module team. Mitigation: additive
changes only within a platform minor version, a deprecation period of at least one release before
removing a component, and a published Storybook so teams do not need to ask what exists.
