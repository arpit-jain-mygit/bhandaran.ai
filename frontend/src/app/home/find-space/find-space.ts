// ---------------------------------------------------------------
// "Find space" form (M1 preview).
// Shows the master-data dropdowns renters will use. Only ACTIVE
// items appear. Picking a state loads that state's cities.
// The actual search arrives in M7.
// ---------------------------------------------------------------
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

import { apiErrorMessage } from '../../core/api-error';
import { City, LookupItem, MasterDataService } from '../../core/master-data.service';

@Component({
  selector: 'app-find-space',
  imports: [FormsModule],
  templateUrl: './find-space.html',
  styleUrl: './find-space.scss',
})
export class FindSpace implements OnInit {
  private readonly api = inject(MasterDataService);

  // Dropdown options.
  protected readonly states = signal<LookupItem[]>([]);
  protected readonly cities = signal<City[]>([]);
  protected readonly storageTypes = signal<LookupItem[]>([]);
  protected readonly stockTypes = signal<LookupItem[]>([]);
  protected readonly error = signal('');

  // Current choices.
  protected stateId = '';
  protected cityId = '';
  protected storageTypeId = '';
  protected stockTypeId = '';

  ngOnInit(): void {
    // Load the three independent lists in parallel.
    forkJoin({
      states: this.api.list('states'),
      storageTypes: this.api.list('storage-types'),
      stockTypes: this.api.list('stock-types'),
    }).subscribe({
      next: (lists) => {
        this.states.set(lists.states);
        this.storageTypes.set(lists.storageTypes);
        this.stockTypes.set(lists.stockTypes);
      },
      error: (error) => this.error.set(apiErrorMessage(error)),
    });
  }

  /** New state picked: reset the city and load that state's cities. */
  protected onStateChange(stateId: string): void {
    this.stateId = stateId;
    this.cityId = '';
    this.cities.set([]);
    if (!stateId) {
      return;
    }
    this.api.listCities(stateId).subscribe({
      next: (cities) => this.cities.set(cities),
      error: (error) => this.error.set(apiErrorMessage(error)),
    });
  }
}
