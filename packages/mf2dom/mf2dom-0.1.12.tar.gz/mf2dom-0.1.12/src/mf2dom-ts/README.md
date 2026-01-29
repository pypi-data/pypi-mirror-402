# mf2dom

Render [Microformats2](https://microformats.org/wiki/microformats2) JSON to semantic HTML.

## Installation

```bash
npm install mf2dom
```

## Usage

### Browser (ESM)

```javascript
import { render, renderItems, renderItemElement } from 'mf2dom';

// Render a full mf2 document
const html = render(mf2Document);

// Render multiple items to a DocumentFragment
const fragment = renderItems(items, { topHeading: 2 });
document.querySelector('main').appendChild(fragment);

// Render a single item to an HTMLElement
const element = renderItemElement(item, { topHeading: 2 });
```

### Browser (IIFE)

```html
<script src="https://unpkg.com/mf2dom/dist/mf2dom.min.js"></script>
<script>
  const html = mf2dom.render(mf2Document);
</script>
```

### Node.js

```javascript
import { render } from 'mf2dom';
import { JSDOM } from 'jsdom';

// Set up global document for Node.js
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
global.document = dom.window.document;

const html = render(mf2Document);
```

## API

### `render(doc, options?)`

Render an mf2 document to HTML.

- `doc`: Microformats2 document with `items` array
- `options.asElement`: Return HTMLElement instead of string (default: false)
- `options.topHeading`: Starting heading level for names (1-6)

### `renderItems(items, options?)`

Render multiple mf2 items to a DocumentFragment.

- `items`: Array of mf2 items
- `options.relUrls`: rel-urls from parsed document
- `options.topHeading`: Starting heading level

### `renderItemElement(item, options?)`

Render a single mf2 item to an HTMLElement.

- `item`: Single mf2 item
- `options.relUrls`: rel-urls from parsed document
- `options.topHeading`: Starting heading level

## Features

- Renders h-entry, h-card, h-feed, h-event, and other microformat types
- Semantic HTML output (article, address, time, etc.)
- Proper heading hierarchy with `topHeading` option
- Handles embedded items (author h-cards, location, etc.)
- Ruby annotations for names with IPA pronunciation
- Linked names when URL matches
- Media handling (photo, video, audio)
- Date/time formatting

## License

AGPL-3.0-or-later
