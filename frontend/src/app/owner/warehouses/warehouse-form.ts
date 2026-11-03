// ---------------------------------------------------------------
// Add or edit a godown listing (M5). Save as a draft, add photos,
// then submit for admin review. Under review, the form is read-only.
// ---------------------------------------------------------------
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { concatMap, forkJoin, of } from 'rxjs';

import { apiErrorMessage } from '../../core/api-error';
import { City, LookupItem, MasterDataService } from '../../core/master-data.service';
import { Warehouse, WarehouseInput, WarehouseService } from '../../core/warehouse.service';
import { GrainLoader } from '../../shared/grain-loader/grain-loader';

@Component({
  selector: 'app-warehouse-form',
  imports: [FormsModule, RouterLink, GrainLoader],
  templateUrl: './warehouse-form.html',
  styleUrl: './warehouse-form.scss',
})
export class WarehouseForm implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly warehouses = inject(WarehouseService);
  private readonly master = inject(MasterDataService);

  protected readonly loading = signal(true);
  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly notice = signal('');
  protected readonly warehouse = signal<Warehouse | null>(null);

  protected cities: City[] = [];
  protected units: LookupItem[] = [];
  protected storageTypes: LookupItem[] = [];
  protected stockTypes: LookupItem[] = [];

  // The form fields. Stock types are a set of checked ids.
  protected name = '';
  protected address = '';
  protected cityId = '';
  protected pincode = '';
  protected capacity: number | null = null;
  protected unitId = '';
  protected storageTypeId = '';
  protected price = '';
  protected stockChecked: Record<string, boolean> = {};

  protected id: string | null = null;

  ngOnInit(): void {
    this.id = this.route.snapshot.paramMap.get('id');
    forkJoin({
      cities: this.master.listCities(),
      units: this.master.list('units'),
      storage: this.master.list('storage-types'),
      stock: this.master.list('stock-types'),
    }).subscribe({
      next: (lookups) => {
        this.cities = lookups.cities;
        this.units = lookups.units;
        this.storageTypes = lookups.storage;
        this.stockTypes = lookups.stock;
        if (this.id) {
          this.load(this.id);
        } else {
          this.loading.set(false);
        }
      },
      error: (error) => {
        this.error.set(apiErrorMessage(error));
        this.loading.set(false);
      },
    });
  }

  /** Required fields still empty, in plain words (empty = ready to save). */
  protected formProblems(): string[] {
    const problems: string[] = [];
    if (!this.name.trim()) problems.push('a name');
    if (!this.address.trim()) problems.push('an address');
    if (!this.cityId) problems.push('a city');
    if (!/^\d{6}$/.test(this.pincode.trim())) problems.push('a 6-digit pincode');
    if (!this.capacity || this.capacity < 1) problems.push('the capacity');
    if (!this.unitId) problems.push('a unit');
    if (!this.storageTypeId) problems.push('a storage type');
    if (!/^\d+(\.\d{1,2})?$/.test(this.price.trim())) problems.push('a price (e.g. 12.50)');
    return problems;
  }

  protected readOnly(): boolean {
    return this.warehouse()?.status === 'PENDING_REVIEW';
  }

  protected save(): void {
    if (this.formProblems().length) return;
    this.busy.set(true);
    this.error.set('');
    this.notice.set('');
    const body = this.inputFromForm();
    const request = this.id ? this.warehouses.update(this.id, body) : this.warehouses.create(body);
    request.subscribe({
      next: (warehouse) => {
        this.busy.set(false);
        this.notice.set('Draft saved.');
        this.show(warehouse);
        if (!this.id) {
          this.router.navigateByUrl(`/owner/warehouses/${warehouse.id}`, { replaceUrl: true });
        }
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(apiErrorMessage(error));
      },
    });
  }

  /** Photo: ask for a link, upload the file to S3, then confirm it. */
  protected addPhoto(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file || !this.id) return;

    this.busy.set(true);
    this.error.set('');
    const id = this.id;
    this.warehouses
      .requestPhoto(id, file.type)
      .pipe(
        concatMap((upload) =>
          this.warehouses
            .uploadFile(upload.upload_url, file)
            .pipe(concatMap(() => this.warehouses.confirmPhoto(id, upload.photo_id))),
        ),
      )
      .subscribe({
        next: (warehouse) => {
          this.busy.set(false);
          this.show(warehouse);
          this.notice.set('Photo added.');
        },
        error: (error) => {
          this.busy.set(false);
          this.error.set(apiErrorMessage(error));
        },
      });
  }

  protected removePhoto(photoId: string): void {
    if (!this.id) return;
    this.busy.set(true);
    this.warehouses.deletePhoto(this.id, photoId).subscribe({
      next: (warehouse) => {
        this.busy.set(false);
        this.show(warehouse);
        this.notice.set('Photo removed.');
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(apiErrorMessage(error));
      },
    });
  }

  protected submit(): void {
    if (!this.id) return;
    this.busy.set(true);
    this.error.set('');
    this.notice.set('');
    this.warehouses.submit(this.id).subscribe({
      next: (warehouse) => {
        this.busy.set(false);
        this.show(warehouse);
        this.notice.set('Sent for review. You will be told when it is approved.');
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(apiErrorMessage(error));
      },
    });
  }

  private load(id: string): void {
    this.warehouses.get(id).subscribe({
      next: (warehouse) => {
        this.show(warehouse);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(apiErrorMessage(error));
        this.loading.set(false);
      },
    });
  }

  /** Copy the server's values into the form. */
  private show(warehouse: Warehouse): void {
    this.warehouse.set(warehouse);
    this.name = warehouse.name;
    this.address = warehouse.address;
    this.cityId = warehouse.city_id;
    this.pincode = warehouse.pincode;
    this.capacity = warehouse.capacity;
    this.unitId = warehouse.unit_id;
    this.storageTypeId = warehouse.storage_type_id;
    this.price = warehouse.price_per_unit_month;
    this.stockChecked = Object.fromEntries(
      warehouse.stock_type_ids.map((stockId) => [stockId, true]),
    );
  }

  private inputFromForm(): WarehouseInput {
    return {
      name: this.name.trim(),
      address: this.address.trim(),
      city_id: this.cityId,
      pincode: this.pincode.trim(),
      capacity: Number(this.capacity),
      unit_id: this.unitId,
      storage_type_id: this.storageTypeId,
      stock_type_ids: Object.keys(this.stockChecked).filter(
        (stockId) => this.stockChecked[stockId],
      ),
      price_per_unit_month: this.price.trim(),
    };
  }
}
