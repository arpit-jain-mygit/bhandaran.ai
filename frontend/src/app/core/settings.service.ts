// ---------------------------------------------------------------
// SettingsService: talks to /api/settings (backend/app/api/settings.py).
// Value precedence: owner override > platform value > code default.
// ---------------------------------------------------------------
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export type SettingValue = boolean | number | string;
export type SettingSource = 'owner' | 'platform' | 'default';

// Same shape as SettingOut in backend/app/schemas/settings.py.
export interface Setting {
  key: string;
  label: string;
  description: string;
  type: 'bool' | 'int' | 'choice';
  choices: string[];
  min: number | null;
  max: number | null;
  owner_can_override: boolean;
  default: SettingValue;
  value: SettingValue; // platform-wide value
  source: 'platform' | 'default';
}

// Same shape as EffectiveSettingOut.
export interface EffectiveSetting {
  key: string;
  label: string;
  value: SettingValue;
  source: SettingSource;
}

const BASE = '/api/settings';

@Injectable({ providedIn: 'root' })
export class SettingsService {
  private readonly http = inject(HttpClient);

  // ---------- platform-wide ----------

  list(): Observable<Setting[]> {
    return this.http.get<Setting[]>(BASE);
  }

  setPlatform(key: string, value: SettingValue): Observable<Setting[]> {
    return this.http.put<Setting[]>(`${BASE}/${key}`, { value });
  }

  resetPlatform(key: string): Observable<Setting[]> {
    return this.http.delete<Setting[]>(`${BASE}/${key}`);
  }

  // ---------- the logged-in owner's own values ----------

  mine(): Observable<EffectiveSetting[]> {
    return this.http.get<EffectiveSetting[]>(`${BASE}/me`);
  }

  setMine(key: string, value: SettingValue): Observable<EffectiveSetting[]> {
    return this.http.put<EffectiveSetting[]>(`${BASE}/me/${key}`, { value });
  }

  resetMine(key: string): Observable<EffectiveSetting[]> {
    return this.http.delete<EffectiveSetting[]>(`${BASE}/me/${key}`);
  }

  // ---------- any owner (admin) ----------

  forOwner(ownerId: string): Observable<EffectiveSetting[]> {
    return this.http.get<EffectiveSetting[]>(`${BASE}/owners/${ownerId}`);
  }

  setOwner(ownerId: string, key: string, value: SettingValue): Observable<EffectiveSetting[]> {
    return this.http.put<EffectiveSetting[]>(`${BASE}/owners/${ownerId}/${key}`, { value });
  }

  resetOwner(ownerId: string, key: string): Observable<EffectiveSetting[]> {
    return this.http.delete<EffectiveSetting[]>(`${BASE}/owners/${ownerId}/${key}`);
  }
}
