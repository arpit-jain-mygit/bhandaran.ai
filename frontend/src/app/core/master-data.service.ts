// ---------------------------------------------------------------
// MasterDataService: talks to /api/master/... (see
// backend/app/api/master.py). Used by dropdowns (read) and by the
// admin screens (read + write).
// ---------------------------------------------------------------
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

// The four simple lists share one shape; the URL name picks the list.
export type LookupKind = 'stock-types' | 'storage-types' | 'units' | 'states';

// Same shape as LookupOut in backend/app/schemas/master.py.
export interface LookupItem {
  id: string;
  code: string;
  name: string;
  sort_order: number;
  is_active: boolean;
}

// Same shape as CityOut.
export interface City {
  id: string;
  state_id: string;
  name: string;
  is_active: boolean;
}

// Bodies for create / partial update.
export interface LookupCreate {
  code: string;
  name: string;
  sort_order: number;
}
export type LookupUpdate = Partial<Pick<LookupItem, 'name' | 'sort_order' | 'is_active'>>;
export type CityUpdate = Partial<Pick<City, 'name' | 'is_active'>>;

const BASE = '/api/master';

@Injectable({ providedIn: 'root' })
export class MasterDataService {
  private readonly http = inject(HttpClient);

  // ---------- simple lists ----------

  /** Active items only (for dropdowns), or everything (for admin). */
  list(kind: LookupKind, includeInactive = false): Observable<LookupItem[]> {
    return this.http.get<LookupItem[]>(`${BASE}/${kind}`, {
      params: { include_inactive: includeInactive },
    });
  }

  create(kind: LookupKind, body: LookupCreate): Observable<LookupItem> {
    return this.http.post<LookupItem>(`${BASE}/${kind}`, body);
  }

  update(kind: LookupKind, id: string, changes: LookupUpdate): Observable<LookupItem> {
    return this.http.patch<LookupItem>(`${BASE}/${kind}/${id}`, changes);
  }

  // ---------- cities ----------

  /** Cities of one state (or all states if stateId is omitted). */
  listCities(stateId?: string, includeInactive = false): Observable<City[]> {
    const params: Record<string, string | boolean> = { include_inactive: includeInactive };
    if (stateId) {
      params['state_id'] = stateId;
    }
    return this.http.get<City[]>(`${BASE}/cities`, { params });
  }

  createCity(stateId: string, name: string): Observable<City> {
    return this.http.post<City>(`${BASE}/cities`, { state_id: stateId, name });
  }

  updateCity(id: string, changes: CityUpdate): Observable<City> {
    return this.http.patch<City>(`${BASE}/cities/${id}`, changes);
  }
}
