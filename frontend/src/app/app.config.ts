// ---------------------------------------------------------------
// App-wide providers (set up once at startup).
// ---------------------------------------------------------------
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { adminKeyInterceptor } from './core/admin-key';

export const appConfig: ApplicationConfig = {
  providers: [
    // Log uncaught errors to the console.
    provideBrowserGlobalErrorListeners(),
    // Page navigation using the routes in app.routes.ts.
    provideRouter(routes),
    // HttpClient for calling the FastAPI backend (uses browser fetch).
    // The interceptor adds the temporary admin key to admin writes.
    provideHttpClient(withFetch(), withInterceptors([adminKeyInterceptor])),
  ],
};
