// ---------------------------------------------------------------
// One approved godown (M7): photos, address, space and price.
// Booking from here arrives with M8/M9.
// ---------------------------------------------------------------
import { Location } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { apiErrorMessage } from '../core/api-error';
import { SearchDetail, SearchService } from '../core/search.service';
import { GrainLoader } from '../shared/grain-loader/grain-loader';

@Component({
  selector: 'app-godown-detail',
  imports: [RouterLink, GrainLoader],
  templateUrl: './godown-detail.html',
  styleUrl: './godown-detail.scss',
})
export class GodownDetail implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(SearchService);
  private readonly location = inject(Location);

  protected readonly godown = signal<SearchDetail | null>(null);
  protected readonly loading = signal(true);
  protected readonly error = signal('');

  protected back(): void {
    this.location.back();
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.api.detail(id).subscribe({
      next: (godown) => {
        this.godown.set(godown);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(apiErrorMessage(error));
        this.loading.set(false);
      },
    });
  }
}
