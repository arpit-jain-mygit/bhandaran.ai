// ---------------------------------------------------------------
// Home page: system status card (M0) + "Find space" dropdowns (M1).
// Later milestones replace this with real owner / renter screens.
// ---------------------------------------------------------------
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { catchError, map, of, startWith } from 'rxjs';

import { Health, HealthService } from '../core/health.service';
import { GrainLoader } from '../shared/grain-loader/grain-loader';
import { FindSpace } from './find-space/find-space';

// The three states the page can be in.
type HealthState = { kind: 'loading' } | { kind: 'loaded'; health: Health } | { kind: 'error' };

@Component({
  selector: 'app-home',
  imports: [FindSpace, GrainLoader],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {
  private readonly healthService = inject(HealthService);

  // Call the API once; turn the result into a signal the template reads.
  // startWith -> "loading" until the response arrives.
  // catchError -> "error" if the API is down (e.g. FastAPI not started).
  protected readonly state = toSignal(
    this.healthService.getHealth().pipe(
      map((health): HealthState => ({ kind: 'loaded', health })),
      catchError(() => of<HealthState>({ kind: 'error' })),
      startWith<HealthState>({ kind: 'loading' }),
    ),
    { requireSync: true },
  );
}
