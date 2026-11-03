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

// Same shape as DistrictOut. A district belongs to a state.
export interface District {
  id: string;
  state_id: string;
  name: string;
  is_active: boolean;
}

// Same shape as CityOut. A city / town belongs to a district.
export interface City {
  id: string;
  district_id: string;
  state_id: string; // derived from the district
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
export type DistrictUpdate = Partial<Pick<District, 'name' | 'is_active'>>;
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

  // ---------- districts (state > district) ----------

  /** Districts of one state (or all if stateId is omitted). */
  listDistricts(stateId?: string, includeInactive = false): Observable<District[]> {
    const params: Record<string, string | boolean> = { include_inactive: includeInactive };
    if (stateId) {
      params['state_id'] = stateId;
    }
    return this.http.get<District[]>(`${BASE}/districts`, { params });
  }

  createDistrict(stateId: string, name: string): Observable<District> {
    return this.http.post<District>(`${BASE}/districts`, { state_id: stateId, name });
  }

  updateDistrict(id: string, changes: DistrictUpdate): Observable<District> {
    return this.http.patch<District>(`${BASE}/districts/${id}`, changes);
  }

  // ---------- cities / towns (district > city) ----------

  /** Cities / towns, filtered by district and/or state. */
  listCities(
    filter: { districtId?: string; stateId?: string } = {},
    includeInactive = false,
  ): Observable<City[]> {
    const params: Record<string, string | boolean> = { include_inactive: includeInactive };
    if (filter.districtId) {
      params['district_id'] = filter.districtId;
    }
    if (filter.stateId) {
      params['state_id'] = filter.stateId;
    }
    return this.http.get<City[]>(`${BASE}/cities`, { params });
  }

  createCity(districtId: string, name: string): Observable<City> {
    return this.http.post<City>(`${BASE}/cities`, { district_id: districtId, name });
  }

  updateCity(id: string, changes: CityUpdate): Observable<City> {
    return this.http.patch<City>(`${BASE}/cities/${id}`, changes);
  }
}
