// ---------------------------------------------------------------
// Admin > Master data (M1).
// One screen with tabs: stock types, storage types, units, states,
// districts, cities / towns. Admins can add, rename, reorder and
// disable/enable items. Nothing is ever deleted.
//
// Location tabs follow the hierarchy state > district > city/town:
//   Districts tab      - pick a state, manage its districts
//   Cities / Towns tab - pick a state, then a district, manage its towns
// ---------------------------------------------------------------
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';

import { AdminKeyStore } from '../../core/admin-key';
import { apiErrorMessage } from '../../core/api-error';
import {
  District,
  LookupItem,
  LookupKind,
  MasterDataService,
} from '../../core/master-data.service';

// Location tabs (rows are just name + active flag).
type PlaceKind = 'districts' | 'cities';
type TabKind = LookupKind | PlaceKind;

// One row on a location tab.
interface PlaceRow {
  id: string;
  name: string;
  is_active: boolean;
}

interface Tab {
  kind: TabKind;
  label: string;
}

export const TABS: Tab[] = [
  { kind: 'stock-types', label: 'Stock types' },
  { kind: 'storage-types', label: 'Storage types' },
  { kind: 'units', label: 'Units' },
  { kind: 'states', label: 'States' },
  { kind: 'districts', label: 'Districts' },
  { kind: 'cities', label: 'Cities / Towns' },
];

@Component({
  selector: 'app-master-data-admin',
  imports: [FormsModule],
  templateUrl: './master-data-admin.html',
  styleUrl: './master-data-admin.scss',
})
export class MasterDataAdmin implements OnInit {
  private readonly api = inject(MasterDataService);
  protected readonly adminKey = inject(AdminKeyStore);

  protected readonly tabs = TABS;
  protected readonly tab = signal<TabKind>('stock-types');

  // Data shown in the table.
  protected readonly items = signal<LookupItem[]>([]); // simple-list tabs
  protected readonly places = signal<PlaceRow[]>([]); // districts / cities tabs

  // Pickers on the location tabs.
  protected readonly states = signal<LookupItem[]>([]);
  protected readonly stateId = signal<string>('');
  protected readonly districts = signal<District[]>([]);
  protected readonly districtId = signal<string>('');

  // Feedback for the admin.
  protected readonly loading = signal(false);
  protected readonly error = signal('');
  protected readonly notice = signal('');

  // "Add" form fields (bound with ngModel).
  protected keyInput = this.adminKey.key();
  protected newCode = '';
  protected newName = '';
  protected newSortOrder = 0;

  // Row being edited (only one at a time).
  protected readonly editingId = signal<string | null>(null);
  protected editName = '';
  protected editSortOrder = 0;

  ngOnInit(): void {
    this.loadStates();
    this.load();
  }

  // ---------- navigation ----------

  protected selectTab(kind: TabKind): void {
    this.tab.set(kind);
    this.cancelEdit();
    this.clearMessages();
    this.load();
  }

  /** True on the Districts and Cities / Towns tabs. */
  protected isPlaceTab(): boolean {
    const kind = this.tab();
    return kind === 'districts' || kind === 'cities';
  }

  protected selectState(stateId: string): void {
    this.stateId.set(stateId);
    this.loadDistricts();
  }

  protected selectDistrict(districtId: string): void {
    this.districtId.set(districtId);
    this.load();
  }

  protected saveKey(): void {
    this.adminKey.set(this.keyInput);
    this.notice.set(this.keyInput.trim() ? 'Admin key saved for this tab.' : 'Admin key cleared.');
  }

  // ---------- loading ----------

  /** States feed the location tabs' state picker (all, incl. disabled). */
  private loadStates(): void {
    this.api.list('states', true).subscribe({
      next: (states) => {
        this.states.set(states);
        if (!this.stateId() && states.length) {
          this.stateId.set(states[0].id);
          this.loadDistricts();
        }
      },
      error: (error) => this.error.set(apiErrorMessage(error)),
    });
  }

  /** Districts of the picked state feed the Cities / Towns tab's picker. */
  private loadDistricts(): void {
    this.api.listDistricts(this.stateId(), true).subscribe({
      next: (districts) => {
        this.districts.set(districts);
        this.districtId.set(districts[0]?.id ?? '');
        this.load();
      },
      error: (error) => this.error.set(apiErrorMessage(error)),
    });
  }

  /** Reload the table for the current tab (disabled items included). */
  protected load(): void {
    const kind = this.tab();
    this.loading.set(true);

    if (kind === 'districts') {
      this.api.listDistricts(this.stateId(), true).subscribe({
        next: (rows) => this.done(() => this.places.set(rows)),
        error: (error) => this.fail(error),
      });
    } else if (kind === 'cities') {
      // No district picked (state has none yet) -> nothing to show.
      if (!this.districtId()) {
        this.done(() => this.places.set([]));
        return;
      }
      this.api.listCities({ districtId: this.districtId() }, true).subscribe({
        next: (rows) => this.done(() => this.places.set(rows)),
        error: (error) => this.fail(error),
      });
    } else {
      this.api.list(kind, true).subscribe({
        next: (items) => this.done(() => this.items.set(items)),
        error: (error) => this.fail(error),
      });
    }
  }

  // ---------- add ----------

  protected add(): void {
    const kind = this.tab();
    this.clearMessages();

    let request: Observable<unknown>;
    if (kind === 'districts') {
      request = this.api.createDistrict(this.stateId(), this.newName);
    } else if (kind === 'cities') {
      request = this.api.createCity(this.districtId(), this.newName);
    } else {
      request = this.api.create(kind, {
        code: this.newCode,
        name: this.newName,
        sort_order: Number(this.newSortOrder) || 0,
      });
    }

    // A new district should show up in the Cities / Towns picker too.
    const after = () => {
      if (kind === 'districts') {
        this.api.listDistricts(this.stateId(), true).subscribe((d) => this.districts.set(d));
      }
    };

    this.run(request, `Added "${this.newName.trim()}".`, () => {
      after();
      this.newCode = '';
      this.newName = '';
      this.newSortOrder = 0;
    });
  }

  // ---------- edit ----------

  protected startEdit(row: { id: string; name: string; sort_order?: number }): void {
    this.editingId.set(row.id);
    this.editName = row.name;
    this.editSortOrder = row.sort_order ?? 0;
  }

  protected cancelEdit(): void {
    this.editingId.set(null);
  }

  protected saveEdit(id: string): void {
    const kind = this.tab();
    this.clearMessages();

    let request: Observable<unknown>;
    if (kind === 'districts') {
      request = this.api.updateDistrict(id, { name: this.editName });
    } else if (kind === 'cities') {
      request = this.api.updateCity(id, { name: this.editName });
    } else {
      request = this.api.update(kind, id, {
        name: this.editName,
        sort_order: Number(this.editSortOrder) || 0,
      });
    }

    this.run(request, 'Saved.', () => this.cancelEdit());
  }

  // ---------- disable / enable ----------

  protected toggleActive(row: { id: string; name: string; is_active: boolean }): void {
    const kind = this.tab();
    const changes = { is_active: !row.is_active };
    this.clearMessages();

    let request: Observable<unknown>;
    if (kind === 'districts') {
      request = this.api.updateDistrict(row.id, changes);
    } else if (kind === 'cities') {
      request = this.api.updateCity(row.id, changes);
    } else {
      request = this.api.update(kind, row.id, changes);
    }

    this.run(request, `${row.is_active ? 'Disabled' : 'Enabled'} "${row.name}".`);
  }

  // ---------- helpers ----------

  /** Send a write, then show a message and reload the table. */
  private run(request: Observable<unknown>, successMessage: string, after?: () => void): void {
    request.subscribe({
      next: () => {
        after?.();
        this.notice.set(successMessage);
        this.load();
      },
      error: (error) => this.error.set(apiErrorMessage(error)),
    });
  }

  private done(apply: () => void): void {
    apply();
    this.loading.set(false);
  }

  private fail(error: unknown): void {
    this.error.set(apiErrorMessage(error));
    this.loading.set(false);
  }

  private clearMessages(): void {
    this.error.set('');
    this.notice.set('');
  }
}
