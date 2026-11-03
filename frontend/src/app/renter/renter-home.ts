// ---------------------------------------------------------------
// Renter's main screen (M3, M8): welcome banner and my bookings.
// A booking an owner recorded offline may need my confirmation.
// ---------------------------------------------------------------
import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { apiErrorMessage } from '../core/api-error';
import { AuthService } from '../core/auth.service';
import { Booking, BookingService, bookingStatusLabel } from '../core/booking.service';
import { GrainLoader } from '../shared/grain-loader/grain-loader';
import { WelcomeBanner } from '../shared/welcome-banner/welcome-banner';

@Component({
  selector: 'app-renter-home',
  imports: [RouterLink, DatePipe, GrainLoader, WelcomeBanner],
  templateUrl: './renter-home.html',
  styleUrl: './renter-home.scss',
})
export class RenterHome implements OnInit {
  protected readonly auth = inject(AuthService);
  private readonly bookings = inject(BookingService);

  protected readonly rows = signal<Booking[]>([]);
  protected readonly loading = signal(true);
  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly statusLabel = bookingStatusLabel;

  ngOnInit(): void {
    this.bookings.mine().subscribe({
      next: (rows) => {
        this.rows.set(rows);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(apiErrorMessage(error));
        this.loading.set(false);
      },
    });
  }

  protected confirm(booking: Booking): void {
    this.busy.set(true);
    this.error.set('');
    this.bookings.confirm(booking.id).subscribe({
      next: (updated) => {
        this.busy.set(false);
        this.rows.update((rows) => rows.map((row) => (row.id === updated.id ? updated : row)));
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(apiErrorMessage(error));
      },
    });
  }
}
