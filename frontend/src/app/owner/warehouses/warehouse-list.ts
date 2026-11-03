// ---------------------------------------------------------------
// My godowns (M5): the owner's listings, their status, and what is
// still missing before each can be submitted for review.
// ---------------------------------------------------------------
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { apiErrorMessage } from '../../core/api-error';
import { Warehouse, WarehouseService } from '../../core/warehouse.service';
import { GrainLoader } from '../../shared/grain-loader/grain-loader';

@Component({
  selector: 'app-warehouse-list',
  imports: [RouterLink, GrainLoader],
  templateUrl: './warehouse-list.html',
  styleUrl: './warehouse-list.scss',
})
export class WarehouseList implements OnInit {
  private readonly warehouses = inject(WarehouseService);

  protected readonly rows = signal<Warehouse[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal('');

  ngOnInit(): void {
    this.warehouses.list().subscribe({
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

  protected statusLabel(warehouse: Warehouse): string {
    return warehouse.status === 'PENDING_REVIEW' ? 'Waiting for review' : 'Draft';
  }
}
