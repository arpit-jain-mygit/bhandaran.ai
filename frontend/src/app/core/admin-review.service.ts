// ---------------------------------------------------------------
// AdminReviewService: talks to /api/admin/warehouses
// (backend/app/api/admin_warehouse.py). Admins approve listings, or
// send them back to the owner with a reason.
// ---------------------------------------------------------------
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Warehouse } from './warehouse.service';

export type ReviewStatus = 'PENDING_REVIEW' | 'APPROVED' | 'DRAFT';

const BASE = '/api/admin/warehouses';

@Injectable({ providedIn: 'root' })
export class AdminReviewService {
  private readonly http = inject(HttpClient);

  list(status: ReviewStatus = 'PENDING_REVIEW'): Observable<Warehouse[]> {
    return this.http.get<Warehouse[]>(BASE, { params: { status } });
  }

  approve(id: string): Observable<Warehouse> {
    return this.http.post<Warehouse>(`${BASE}/${id}/approve`, {});
  }

  reject(id: string, reason: string): Observable<Warehouse> {
    return this.http.post<Warehouse>(`${BASE}/${id}/reject`, { reason });
  }
}
