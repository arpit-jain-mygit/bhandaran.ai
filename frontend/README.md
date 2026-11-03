# frontend - Angular web app for bhandaran.ai

Angular 22 (standalone components, signals), Vitest for unit tests.

## Run

```bash
npm install
```

```bash
npx ng serve
```

Open http://localhost:4200. Calls to `/api/...` are forwarded to FastAPI on port 8000 by [proxy.conf.mjs](proxy.conf.mjs), so start the backend first.

## Layout

```
src/app/
├── app.ts / app.html     shell: header + <router-outlet>
├── app.routes.ts         URL -> page mapping
├── app.config.ts         router + HttpClient providers
├── core/                 shared services (HealthService)
└── home/                 Home page: system status card
```

Colour tokens (light + dark) live in `src/styles.scss`.

## Checks

```bash
npx ng build
```

```bash
npx ng test --watch=false
```
