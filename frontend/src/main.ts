// ---------------------------------------------------------------
// Browser entry point: starts the Angular app with the root
// component (App) and the providers in app.config.ts.
// ---------------------------------------------------------------
import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

bootstrapApplication(App, appConfig).catch((err) => console.error(err));
