// ---------------------------------------------------------------
// HealthService: asks the FastAPI backend "are you up, and can you
// reach the database?" via GET /api/health.
// ---------------------------------------------------------------
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

// Same shape as HealthResponse in backend/app/api/health.py.
export interface Health {
  status: 'ok' | 'degraded';
  version: string;
  db_mode: string;
  database: 'ok' | 'unreachable';
}

// providedIn: 'root' = one shared instance for the whole app.
@Injectable({ providedIn: 'root' })
export class HealthService {
  private readonly http = inject(HttpClient);

  // Relative URL: the dev proxy (proxy.conf.mjs) forwards it to FastAPI.
  getHealth(): Observable<Health> {
    return this.http.get<Health>('/api/health');
  }
}
