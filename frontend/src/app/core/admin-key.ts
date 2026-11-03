// ---------------------------------------------------------------
// TEMPORARY admin key handling (until M3 adds real login).
//
// AdminKeyStore  - remembers the key for this browser tab only
//                  (sessionStorage: cleared when the tab closes).
// adminKeyInterceptor - adds "X-Admin-Key: <key>" to every
//                  non-GET request to /api/master.
// ---------------------------------------------------------------
import { HttpInterceptorFn } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';

const STORAGE_KEY = 'bhandaran.adminKey';

// Browser storage can be blocked (private mode, strict settings),
// so every access is wrapped in try/catch.
function readStored(): string {
  try {
    return sessionStorage.getItem(STORAGE_KEY) ?? '';
  } catch {
    return '';
  }
}

@Injectable({ providedIn: 'root' })
export class AdminKeyStore {
  /** Current key ('' = none). Components read it as a signal. */
  readonly key = signal(readStored());

  set(value: string): void {
    const trimmed = value.trim();
    this.key.set(trimmed);
    try {
      if (trimmed) {
        sessionStorage.setItem(STORAGE_KEY, trimmed);
      } else {
        sessionStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // Not stored: the key still works until the page reloads.
    }
  }
}

export const adminKeyInterceptor: HttpInterceptorFn = (request, next) => {
  const key = inject(AdminKeyStore).key();
  const isAdminWrite = request.method !== 'GET' && request.url.startsWith('/api/master');

  if (isAdminWrite && key) {
    return next(request.clone({ setHeaders: { 'X-Admin-Key': key } }));
  }
  return next(request);
};
