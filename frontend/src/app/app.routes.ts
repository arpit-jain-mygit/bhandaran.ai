// ---------------------------------------------------------------
// URL -> page mapping. Each milestone adds its pages here.
// ---------------------------------------------------------------
import { Routes } from '@angular/router';

import { roleGuard } from './core/auth.guard';
import { Home } from './home/home';

export const routes: Routes = [
  // "/" - system status + "Find space" dropdowns.
  { path: '', component: Home, title: 'bhandaran.ai' },

  // "/login" - phone OTP login and sign-up (M3).
  {
    path: 'login',
    title: 'Log in - bhandaran.ai',
    loadComponent: () => import('./auth/login/login').then((m) => m.Login),
  },

  // "/owner" - owner's main screen, owners only (M3).
  {
    path: 'owner',
    title: 'Owner - bhandaran.ai',
    canActivate: [roleGuard('OWNER')],
    loadComponent: () => import('./owner/owner-home').then((m) => m.OwnerHome),
  },

  // "/renter" - renter's main screen, renters only (M3).
  {
    path: 'renter',
    title: 'Renter - bhandaran.ai',
    canActivate: [roleGuard('RENTER')],
    loadComponent: () => import('./renter/renter-home').then((m) => m.RenterHome),
  },

  // "/admin/master-data" - manage lists (M1). Admins only.
  {
    path: 'admin/master-data',
    title: 'Master data - bhandaran.ai',
    canActivate: [roleGuard('ADMIN')],
    loadComponent: () =>
      import('./admin/master-data/master-data-admin').then((m) => m.MasterDataAdmin),
  },

  // "/admin/settings" - platform settings + owner overrides (M2). Admins only.
  {
    path: 'admin/settings',
    title: 'Platform settings - bhandaran.ai',
    canActivate: [roleGuard('ADMIN')],
    loadComponent: () => import('./admin/settings/settings-admin').then((m) => m.SettingsAdmin),
  },

  // Any unknown URL goes back to Home.
  { path: '**', redirectTo: '' },
];
