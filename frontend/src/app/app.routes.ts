// ---------------------------------------------------------------
// URL -> page mapping. Each milestone adds its pages here.
// ---------------------------------------------------------------
import { Routes } from '@angular/router';

import { Home } from './home/home';

export const routes: Routes = [
  // "/" shows the Home page (system status in M0).
  { path: '', component: Home },
  // Any unknown URL goes back to Home.
  { path: '**', redirectTo: '' },
];
