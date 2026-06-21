# rrg-data
RRG live data, plus a personal AI companion.

## Pages (GitHub Pages, served from `docs/`)
- **`docs/index.html`** — Rotation Terminal (RRG) dashboard.
- **`docs/companion.html`** — Companion: a 24/7, voice-and-text AI companion with a
  customizable persona and persistent memory. It runs entirely in your browser and
  talks directly to the Anthropic API using your own key (stored locally, never sent
  anywhere except Anthropic). Open it, paste an Anthropic API key, and start talking.

### Companion notes
- **Always available:** it's a static page, so once deployed it's reachable 24/7 from
  any device — phone or laptop — at `https://<user>.github.io/rrg-data/companion.html`.
- **Voice both ways:** speech-to-text via the browser's Web Speech API (Chrome/Edge),
  and spoken replies via the browser's text-to-speech.
- **Memory:** conversation history and an editable "what it remembers about you" note
  persist in the browser. The companion adds durable facts to memory on its own.
- **Make it yours:** name, personality, model, and voice are all editable in Settings.
- **Cost:** each message is a normal Anthropic API call billed to your key. Pick Haiku
  in Settings for the snappiest voice conversations.
