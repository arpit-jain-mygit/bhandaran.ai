// ---------------------------------------------------------------
// Search results (M7): approved godowns matching the filters in the
// URL (set by the Find space form on Home). Cheapest first.
// ---------------------------------------------------------------
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { apiErrorMessage } from '../core/api-error';
import { SearchResult, SearchService } from '../core/search.service';
import { GrainLoader } from '../shared/grain-loader/grain-loader';
import { Icon } from '../shared/icon/icon';

// Only these URL parameters are sent to the API.
const FILTERS = [
  'state_id',
  'district_id',
  'city_id',
  'pincode',
  'storage_type_id',
  'stock_type_id',
  'max_price',
  'min_capacity',
];

@Component({
  selector: 'app-search-results',
  imports: [RouterLink, GrainLoader, Icon],
  templateUrl: './search-results.html',
  styleUrl: './search-results.scss',
})
export class SearchResults implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(SearchService);

  protected readonly rows = signal<SearchResult[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal('');

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      const filters: Record<string, string> = {};
      for (const key of FILTERS) {
        const value = params.get(key);
        if (value) filters[key] = value;
      }
      this.run(filters);
    });
  }

  private run(filters: Record<string, string>): void {
    this.loading.set(true);
    this.error.set('');
    this.api.search(filters).subscribe({
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
