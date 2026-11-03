// ---------------------------------------------------------------
// BookingService: talks to /api/bookings (backend/app/api/booking.py).
// Owners record offline bookings; renters see and confirm theirs.
// ---------------------------------------------------------------
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export type BookingStatus = 'PENDING_RENTER_CONFIRMATION' | 'CONFIRMED' | 'ACTIVE';

// Same shape as BookingOut in backend/app/schemas/booking.py.
export interface Booking {
  id: string;
  warehouse_id: string;
  warehouse_name: string;
  city_name: string | null;
  owner_name: string | null;
  renter_name: string | null;
  renter_email: string | null;
  stock_type_name: string | null;
  unit_name: string | null;
  quantity: number;
  start_date: string; // YYYY-MM-DD
  end_date: string;
  rate_per_unit_month: string;
  channel: 'OFFLINE' | 'ONLINE';
  status: BookingStatus;
  unverified: boolean;
  confirmation_due_at: string | null;
  confirmed_at: string | null;
  created_at: string;
}

export interface OfflineBookingInput {
  warehouse_id: string;
  renter_email: string;
  renter_name: string;
  stock_type_id: string;
  quantity: number;
  start_date: string;
  end_date: string;
  rate_per_unit_month: string;
}

/** Friendly words for a booking's status. */
export function bookingStatusLabel(booking: Booking): string {
  if (booking.status === 'PENDING_RENTER_CONFIRMATION') return 'Waiting for renter';
  const base = booking.status === 'ACTIVE' ? 'Active' : 'Confirmed';
  return booking.unverified ? `${base} (not verified by renter)` : base;
}

const BASE = '/api/bookings';

@Injectable({ providedIn: 'root' })
export class BookingService {
  private readonly http = inject(HttpClient);

  record(body: OfflineBookingInput): Observable<Booking> {
    return this.http.post<Booking>(BASE, body);
  }

  forOwner(): Observable<Booking[]> {
    return this.http.get<Booking[]>(`${BASE}/owner`);
  }

  mine(): Observable<Booking[]> {
    return this.http.get<Booking[]>(`${BASE}/mine`);
  }

  confirm(id: string): Observable<Booking> {
    return this.http.post<Booking>(`${BASE}/${id}/confirm`, {});
  }
}
