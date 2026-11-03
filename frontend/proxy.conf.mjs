// ---------------------------------------------------------------
// Dev-server proxy (used only by `ng serve`).
// The browser calls /api/... on the Angular port (4200); the dev
// server forwards it to FastAPI on port 8000. This avoids CORS
// issues locally and keeps the same relative URLs as production.
// ---------------------------------------------------------------
export default {
  '/api': {
    target: 'http://localhost:8000',
    secure: false,
    changeOrigin: true,
  },
};
