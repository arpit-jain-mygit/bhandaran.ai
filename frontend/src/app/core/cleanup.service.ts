// ---------------------------------------------------------------
// CleanupService: talks to /api/admin/test-data
// (backend/app/api/admin_test_data.py). Admins preview, then delete,
// test accounts and godowns with everything that belongs to them.
// ---------------------------------------------------------------
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

// Same shape as CleanupOut in backend/app/schemas/cleanup.py.
export interface CleanupPlan {
  accounts: string[];
  missing_emails: string[];
  warehouses: number;
  missing_warehouse_ids: string[];
  bookings: number;
  photos: number;
  login_codes: number;
  owner_settings: number;
  suppressed_emails: number;
  invitees_released: number;
  deleted: boolean;
  photo_files_left: number;
}

export interface CleanupRequest {
  emails: string[];
  warehouse_ids: string[];
}

const BASE = '/api/admin/test-data';

@Injectable({ providedIn: 'root' })
export class CleanupService {
  private readonly http = inject(HttpClient);

  preview(request: CleanupRequest): Observable<CleanupPlan> {
    return this.http.post<CleanupPlan>(`${BASE}/preview`, request);
  }

  remove(request: CleanupRequest): Observable<CleanupPlan> {
    return this.http.post<CleanupPlan>(`${BASE}/delete`, { ...request, confirm: 'DELETE' });
  }
}
