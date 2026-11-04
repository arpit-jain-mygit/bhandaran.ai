// ---------------------------------------------------------------
// URL -> page mapping. Each milestone adds its pages here.
// ---------------------------------------------------------------
import { Routes } from '@angular/router';

import { roleGuard } from './core/auth.guard';
import { Home } from './home/home';

export const routes: Routes = [
  // "/" - system status + "Find space" dropdowns.
  { path: '', component: Home, title: 'bhandaran.ai' },

  // "/search" - approved godowns matching the Home filters (M7). Public.
  {
    path: 'search',
    title: 'Search - bhandaran.ai',
    loadComponent: () => import('./search/search-results').then((m) => m.SearchResults),
  },

  // "/godowns/:id" - one approved godown (M7). Public.
  {
    path: 'godowns/:id',
    title: 'Godown - bhandaran.ai',
    loadComponent: () => import('./search/godown-detail').then((m) => m.GodownDetail),
  },

  // "/login" - email OTP login and sign-up (M3).
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

  // "/profile" - my name, city and GST number (M4). Any logged-in role.
  {
    path: 'profile',
    title: 'My profile - bhandaran.ai',
    canActivate: [roleGuard('OWNER', 'RENTER', 'ADMIN')],
    loadComponent: () => import('./profile/profile-page').then((m) => m.ProfilePage),
  },

  // "/owner/warehouses" - the owner's godown listings (M5).
  {
    path: 'owner/warehouses',
    title: 'My godowns - bhandaran.ai',
    canActivate: [roleGuard('OWNER')],
    loadComponent: () => import('./owner/warehouses/warehouse-list').then((m) => m.WarehouseList),
  },
  {
    path: 'owner/warehouses/new',
    title: 'Add a godown - bhandaran.ai',
    canActivate: [roleGuard('OWNER')],
    loadComponent: () => import('./owner/warehouses/warehouse-form').then((m) => m.WarehouseForm),
  },
  {
    path: 'owner/warehouses/:id',
    title: 'Edit godown - bhandaran.ai',
    canActivate: [roleGuard('OWNER')],
    loadComponent: () => import('./owner/warehouses/warehouse-form').then((m) => m.WarehouseForm),
  },

  // "/owner/bookings" - bookings at my godowns + record offline deals (M8).
  {
    path: 'owner/bookings',
    title: 'Bookings - bhandaran.ai',
    canActivate: [roleGuard('OWNER')],
    loadComponent: () => import('./owner/bookings/owner-bookings').then((m) => m.OwnerBookings),
  },

  // "/renter" - renter's main screen, renters only (M3).
  {
    path: 'renter',
    title: 'Renter - bhandaran.ai',
    canActivate: [roleGuard('RENTER')],
    loadComponent: () => import('./renter/renter-home').then((m) => m.RenterHome),
  },

  // "/admin" - admin home: the review queue.
  { path: 'admin', pathMatch: 'full', redirectTo: 'admin/listings' },

  // "/admin/master-data" - manage lists (M1). Admins only.
  {
    path: 'admin/master-data',
    title: 'Master data - bhandaran.ai',
    canActivate: [roleGuard('ADMIN')],
    loadComponent: () =>
      import('./admin/master-data/master-data-admin').then((m) => m.MasterDataAdmin),
  },

  // "/admin/listings" - review owners' godown listings (M6). Admins only.
  {
    path: 'admin/listings',
    title: 'Review listings - bhandaran.ai',
    canActivate: [roleGuard('ADMIN')],
    loadComponent: () => import('./admin/listings/listings-admin').then((m) => m.ListingsAdmin),
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
