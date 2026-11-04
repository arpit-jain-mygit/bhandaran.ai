// ---------------------------------------------------------------
// Admin > Listings (M6): check each godown an owner submitted, then
// approve it or send it back with a reason.
// ---------------------------------------------------------------
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { AdminReviewService, ReviewStatus } from '../../core/admin-review.service';
import { apiErrorMessage } from '../../core/api-error';
import { LookupItem, MasterDataService } from '../../core/master-data.service';
import { Warehouse } from '../../core/warehouse.service';
import { GrainLoader } from '../../shared/grain-loader/grain-loader';
import { AdminHeader } from '../admin-header/admin-header';
import { Icon } from '../../shared/icon/icon';

@Component({
  selector: 'app-listings-admin',
  imports: [FormsModule, GrainLoader, AdminHeader, Icon],
  templateUrl: './listings-admin.html',
  styleUrl: './listings-admin.scss',
})
export class ListingsAdmin implements OnInit {
  private readonly review = inject(AdminReviewService);
  private readonly master = inject(MasterDataService);

  protected readonly tab = signal<ReviewStatus>('PENDING_REVIEW');
  protected readonly rows = signal<Warehouse[]>([]);
  protected readonly loading = signal(true);
  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly notice = signal('');

  // Reason typed for each listing before "Send back".
  protected reasons: Record<string, string> = {};
  private stockNames: Record<string, string> = {};

  ngOnInit(): void {
    this.master.list('stock-types').subscribe((items: LookupItem[]) => {
      this.stockNames = Object.fromEntries(items.map((item) => [item.id, item.name]));
    });
    this.load();
  }

  protected show(tab: ReviewStatus): void {
    this.tab.set(tab);
    this.notice.set('');
    this.load();
  }

  protected stockList(warehouse: Warehouse): string {
    return warehouse.stock_type_ids.map((id) => this.stockNames[id] ?? '?').join(', ');
  }

  protected approve(warehouse: Warehouse): void {
    this.decide(this.review.approve(warehouse.id), `Approved "${warehouse.name}".`);
  }

  protected reject(warehouse: Warehouse): void {
    const reason = (this.reasons[warehouse.id] ?? '').trim();
    this.decide(
      this.review.reject(warehouse.id, reason),
      `Sent "${warehouse.name}" back to the owner.`,
    );
  }

  private decide(request: ReturnType<AdminReviewService['approve']>, message: string): void {
    this.busy.set(true);
    this.error.set('');
    request.subscribe({
      next: () => {
        this.busy.set(false);
        this.notice.set(message);
        this.load();
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(apiErrorMessage(error));
      },
    });
  }

  private load(): void {
    this.loading.set(true);
    this.review.list(this.tab()).subscribe({
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
}
