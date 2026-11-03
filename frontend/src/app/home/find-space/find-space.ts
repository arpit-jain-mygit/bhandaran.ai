// ---------------------------------------------------------------
// "Find space" form (M1 preview).
// Shows the master-data dropdowns renters will use. Only ACTIVE
// items appear. Location is picked top-down:
//   State -> District -> City / Town
// Choosing a level loads the next one and resets everything below.
// The actual search arrives in M7.
// ---------------------------------------------------------------
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Observable, finalize, forkJoin } from 'rxjs';

import { apiErrorMessage } from '../../core/api-error';
import { City, District, LookupItem, MasterDataService } from '../../core/master-data.service';
import { GrainLoader } from '../../shared/grain-loader/grain-loader';

@Component({
  selector: 'app-find-space',
  imports: [FormsModule, GrainLoader],
  templateUrl: './find-space.html',
  styleUrl: './find-space.scss',
})
export class FindSpace implements OnInit {
  private readonly api = inject(MasterDataService);

  // Dropdown options.
  protected readonly states = signal<LookupItem[]>([]);
  protected readonly districts = signal<District[]>([]);
  protected readonly cities = signal<City[]>([]);
  protected readonly storageTypes = signal<LookupItem[]>([]);
  protected readonly stockTypes = signal<LookupItem[]>([]);
  protected readonly error = signal('');

  // How many list requests are still running (> 0 shows the spinner).
  protected readonly pending = signal(0);

  // Current choices.
  protected stateId = '';
  protected districtId = '';
  protected cityId = '';
  protected storageTypeId = '';
  protected stockTypeId = '';

  ngOnInit(): void {
    // Load the three independent lists in parallel.
    this.track(
      forkJoin({
        states: this.api.list('states'),
        storageTypes: this.api.list('storage-types'),
        stockTypes: this.api.list('stock-types'),
      }),
    ).subscribe({
      next: (lists) => {
        this.states.set(lists.states);
        this.storageTypes.set(lists.storageTypes);
        this.stockTypes.set(lists.stockTypes);
      },
      error: (error) => this.error.set(apiErrorMessage(error)),
    });
  }

  /** New state picked: reset district + city, load the state's districts. */
  protected onStateChange(stateId: string): void {
    this.stateId = stateId;
    this.districtId = '';
    this.cityId = '';
    this.districts.set([]);
    this.cities.set([]);
    if (!stateId) {
      return;
    }
    this.track(this.api.listDistricts(stateId)).subscribe({
      next: (districts) => this.districts.set(districts),
      error: (error) => this.error.set(apiErrorMessage(error)),
    });
  }

  /** New district picked: reset the city, load the district's cities / towns. */
  protected onDistrictChange(districtId: string): void {
    this.districtId = districtId;
    this.cityId = '';
    this.cities.set([]);
    if (!districtId) {
      return;
    }
    this.track(this.api.listCities({ districtId })).subscribe({
      next: (cities) => this.cities.set(cities),
      error: (error) => this.error.set(apiErrorMessage(error)),
    });
  }

  /** Count a request as running until it finishes (success or error). */
  private track<T>(request: Observable<T>): Observable<T> {
    this.pending.update((n) => n + 1);
    return request.pipe(finalize(() => this.pending.update((n) => n - 1)));
  }
}
