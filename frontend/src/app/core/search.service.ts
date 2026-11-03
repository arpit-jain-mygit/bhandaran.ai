// ---------------------------------------------------------------
// SearchService: talks to /api/search (backend/app/api/search.py).
// Public: anyone can search approved godowns, no login needed.
// ---------------------------------------------------------------
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

// Same shapes as backend/app/schemas/search.py.
export interface SearchResult {
  id: string;
  name: string;
  city_name: string;
  district_name: string;
  state_name: string;
  pincode: string;
  storage_type_name: string;
  unit_name: string;
  available_capacity: number; // total capacity until bookings (M8)
  price_per_unit_month: string;
  stock_types: string[];
  photo_url: string | null;
}

export interface SearchDetail extends SearchResult {
  address: string;
  capacity: number;
  photo_urls: string[];
}

const BASE = '/api/search/warehouses';

@Injectable({ providedIn: 'root' })
export class SearchService {
  private readonly http = inject(HttpClient);

  /** Filters come straight from the /search URL (only the ones chosen). */
  search(filters: Record<string, string>): Observable<SearchResult[]> {
    return this.http.get<SearchResult[]>(BASE, { params: filters });
  }

  detail(id: string): Observable<SearchDetail> {
    return this.http.get<SearchDetail>(`${BASE}/${id}`);
  }
}
