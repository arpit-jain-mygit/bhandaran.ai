// ---------------------------------------------------------------
// ProfileService: talks to /api/profile (backend/app/api/profile.py).
// Every user edits their own profile; owners can invite renters.
// ---------------------------------------------------------------
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

// Same shape as ProfileOut in backend/app/schemas/profile.py.
export interface Profile {
  id: string;
  email: string | null;
  name: string | null;
  status: 'ACTIVE' | 'SUSPENDED' | 'UNCLAIMED';
  city_id: string | null;
  city_name: string | null;
  gst_number: string | null;
  roles: string[];
}

export interface ProfileChanges {
  name: string;
  city_id: string | null;
  gst_number: string | null;
}

const BASE = '/api/profile';

@Injectable({ providedIn: 'root' })
export class ProfileService {
  private readonly http = inject(HttpClient);

  me(): Observable<Profile> {
    return this.http.get<Profile>(`${BASE}/me`);
  }

  update(changes: ProfileChanges): Observable<Profile> {
    return this.http.put<Profile>(`${BASE}/me`, changes);
  }

  /** Owners only: invite a renter by email. They claim the account by logging in. */
  inviteRenter(email: string, name: string): Observable<Profile> {
    return this.http.post<Profile>(`${BASE}/renters`, { email, name });
  }
}
