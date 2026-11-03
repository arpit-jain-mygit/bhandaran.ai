// ---------------------------------------------------------------
// URL -> page mapping. Each milestone adds its pages here.
// ---------------------------------------------------------------
import { Routes } from '@angular/router';

import { Home } from './home/home';

export const routes: Routes = [
  // "/" - system status + "Find space" dropdowns.
  { path: '', component: Home, title: 'bhandaran.ai' },

  // "/admin/master-data" - manage lists (M1). Loaded only when visited.
  {
    path: 'admin/master-data',
    title: 'Master data - bhandaran.ai',
    loadComponent: () =>
      import('./admin/master-data/master-data-admin').then((m) => m.MasterDataAdmin),
  },

  // Any unknown URL goes back to Home.
  { path: '**', redirectTo: '' },
];
