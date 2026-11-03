// ---------------------------------------------------------------
// AuthService: who is logged in, and the phone-OTP login steps.
// Talks to /api/auth (backend/app/api/auth.py). The session itself
// is an httpOnly cookie the browser sends automatically - this code
// never sees the token.
// ---------------------------------------------------------------
import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, catchError, map, of, shareReplay, tap } from 'rxjs';

export type Role = 'OWNER' | 'RENTER' | 'ADMIN';

export interface User {
  id: string;
  phone: string;
  name: string | null;
  roles: Role[];
}

export interface OtpSent {
  sent: boolean;
  expires_in_seconds: number;
  dev_code: string | null; // local development only
}

export interface VerifyResult {
  status: 'logged_in' | 'signup_required';
  user: User | null;
  signup_token: string | null;
}

const BASE = '/api/auth';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);

  /** undefined = not checked yet, null = logged out, User = logged in. */
  readonly user = signal<User | null | undefined>(undefined);
  readonly loggedIn = computed(() => !!this.user());

  private check$?: Observable<User | null>;

  /** Ask the server once who is logged in (guards wait for this). */
  ensureLoaded(): Observable<User | null> {
    const known = this.user();
    if (known !== undefined) {
      return of(known);
    }
    this.check$ ??= this.http.get<User>(`${BASE}/me`).pipe(
      // 401 (not logged in) or any failure: treat as logged out.
      catchError(() => of(null)),
      tap((user) => this.user.set(user)),
      shareReplay(1),
    );
    return this.check$;
  }

  hasRole(role: Role): boolean {
    return this.user()?.roles.includes(role) ?? false;
  }

  /** Where a user lands after login: their main screen. */
  homeFor(user: User): string {
    if (user.roles.includes('ADMIN')) return '/admin/master-data';
    if (user.roles.includes('OWNER')) return '/owner';
    if (user.roles.includes('RENTER')) return '/renter';
    return '/';
  }

  // ---------- login steps ----------

  requestOtp(phone: string): Observable<OtpSent> {
    return this.http.post<OtpSent>(`${BASE}/otp`, { phone });
  }

  verifyOtp(phone: string, code: string): Observable<VerifyResult> {
    return this.http
      .post<VerifyResult>(`${BASE}/verify`, { phone, code })
      .pipe(tap((result) => result.user && this.user.set(result.user)));
  }

  signup(signupToken: string, name: string, role: 'OWNER' | 'RENTER'): Observable<User> {
    return this.http
      .post<User>(`${BASE}/signup`, { signup_token: signupToken, name, role })
      .pipe(tap((user) => this.user.set(user)));
  }

  logout(): Observable<void> {
    return this.http.post<void>(`${BASE}/logout`, {}).pipe(
      catchError(() => of(undefined)), // log out locally even if the call fails
      map(() => {
        this.user.set(null);
        this.check$ = undefined;
      }),
    );
  }
}
