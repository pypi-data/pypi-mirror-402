# Claude Instructions for logler-web

## Project Type
Vue 3 + TypeScript frontend with FastAPI Python backend.

## Tech Stack
- **Frontend**: Vue 3.5, Naive UI 2.41, Phosphor Icons, Pinia, Vite 6
- **Backend**: FastAPI, Uvicorn, logler package
- **Design**: the-style Cyberpunk design system

## Code Style

### Vue Components
- Use `<script setup lang="ts">` syntax
- Import Naive UI components individually (tree-shaking)
- Use Phosphor icons with explicit weight: `<PhIcon weight="regular" />`
- Store state in Pinia stores, not component state for shared data

### TypeScript
- Strict mode enabled
- Define interfaces in `src/api/types.ts`
- Use `@/` alias for src imports

### Design System
- Import tokens from `@/design/tokens.ts`
- Use `createDsNaiveThemeOverrides()` for Naive UI theming
- Call `providePhosphorDefaults()` in App.vue setup (not onMounted)
- Follow Cyberpunk color palette for log levels

## File Organization
```
src/
├── api/          # API client and types
├── components/   # Vue components by feature
├── composables/  # Vue composables (useXxx)
├── design/       # Design system files
├── stores/       # Pinia stores
└── views/        # Page-level components
```

## API Endpoints
All endpoints are in `backend/app.py`:
- `GET /api/files/browse` - Directory listing
- `GET /api/files/glob` - Glob search
- `POST /api/files/open` - Open single file
- `POST /api/files/open_many` - Open multiple files
- `POST /api/files/filter` - Filter entries
- `GET /api/threads` - Thread list
- `GET /api/traces` - Trace list
- `POST /api/hierarchy` - Build hierarchy
- `POST /api/sql` - Execute SQL query
- `WS /ws` - WebSocket for live following

## Pending Work
1. Hierarchy view - use `NTree` or custom tree component
2. Waterfall view - timeline bars showing duration
3. SQL tab - query editor with `NInput` + results `NDataTable`

## Testing
```bash
# Type check
pnpm type-check

# Build
pnpm build
```

## Don't
- Don't add emojis unless asked
- Don't create new files unless necessary
- Don't use CSS-in-JS, use scoped `<style>` or design tokens
- Don't hardcode colors - use `ds.color.*` tokens
