// ---------------------------------------------------------------
// Owner > Bookings (M8): bookings at my godowns, and a form to record
// a deal made in person or by phone.
// ---------------------------------------------------------------
import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { apiErrorMessage } from '../../core/api-error';
import { Booking, BookingService, bookingStatusLabel } from '../../core/booking.service';
import { LookupItem, MasterDataService } from '../../core/master-data.service';
import { Warehouse, WarehouseService } from '../../core/warehouse.service';
import { GrainLoader } from '../../shared/grain-loader/grain-loader';

@Component({
  selector: 'app-owner-bookings',
  imports: [FormsModule, RouterLink, DatePipe, GrainLoader],
  templateUrl: './owner-bookings.html',
  styleUrl: './owner-bookings.scss',
})
export class OwnerBookings implements OnInit {
  private readonly bookings = inject(BookingService);
  private readonly warehouses = inject(WarehouseService);
  private readonly master = inject(MasterDataService);

  protected readonly rows = signal<Booking[]>([]);
  protected readonly godowns = signal<Warehouse[]>([]); // approved ones only
  protected readonly loading = signal(true);
  protected readonly busy = signal(false);
  protected readonly showForm = signal(false);
  protected readonly error = signal('');
  protected readonly notice = signal('');
  protected readonly statusLabel = bookingStatusLabel;
  private stockNames: Record<string, string> = {};

  // Form fields.
  protected warehouseId = '';
  protected renterEmail = '';
  protected renterName = '';
  protected stockTypeId = '';
  protected quantity: number | null = null;
  protected startDate = '';
  protected endDate = '';
  protected rate = '';

  ngOnInit(): void {
    forkJoin({
      rows: this.bookings.forOwner(),
      godowns: this.warehouses.list(),
      stock: this.master.list('stock-types'),
    }).subscribe({
      next: ({ rows, godowns, stock }) => {
        this.rows.set(rows);
        this.godowns.set(godowns.filter((g) => g.status === 'APPROVED'));
        this.stockNames = Object.fromEntries(stock.map((s: LookupItem) => [s.id, s.name]));
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(apiErrorMessage(error));
        this.loading.set(false);
      },
    });
  }

  protected selectedGodown(): Warehouse | undefined {
    return this.godowns().find((g) => g.id === this.warehouseId);
  }

  protected stockName(id: string): string {
    return this.stockNames[id] ?? id;
  }

  /** New godown picked: suggest its price and clear the stock choice. */
  protected onGodownChange(id: string): void {
    this.warehouseId = id;
    this.stockTypeId = '';
    const godown = this.selectedGodown();
    if (godown) this.rate = godown.price_per_unit_month;
  }

  /** Required fields still empty, in plain words (empty = ready). */
  protected formProblems(): string[] {
    const problems: string[] = [];
    if (!this.warehouseId) problems.push('a godown');
    if (!this.renterEmail.trim()) problems.push("the renter's email");
    if (!this.stockTypeId) problems.push('a stock type');
    if (!this.quantity || this.quantity < 1) problems.push('the space');
    if (!this.startDate || !this.endDate) problems.push('the dates');
    else if (this.endDate < this.startDate) problems.push('an end date after the start');
    if (!/^\d+(\.\d{1,2})?$/.test(this.rate.trim())) problems.push('the agreed rate');
    return problems;
  }

  protected save(): void {
    if (this.formProblems().length) return;
    this.busy.set(true);
    this.error.set('');
    this.notice.set('');
    this.bookings
      .record({
        warehouse_id: this.warehouseId,
        renter_email: this.renterEmail.trim(),
        renter_name: this.renterName.trim(),
        stock_type_id: this.stockTypeId,
        quantity: Number(this.quantity),
        start_date: this.startDate,
        end_date: this.endDate,
        rate_per_unit_month: this.rate.trim(),
      })
      .subscribe({
        next: (booking) => {
          this.busy.set(false);
          this.rows.update((rows) => [booking, ...rows]);
          this.notice.set(
            booking.status === 'PENDING_RENTER_CONFIRMATION'
              ? `Booking saved. ${booking.renter_email} has been asked to confirm it.`
              : 'Booking saved.',
          );
          this.showForm.set(false);
          this.renterEmail = this.renterName = '';
          this.quantity = null;
        },
        error: (error) => {
          this.busy.set(false);
          this.error.set(apiErrorMessage(error));
        },
      });
  }
}
