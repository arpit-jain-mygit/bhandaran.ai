// ---------------------------------------------------------------
// Owner's main screen (M3). Booking rules are set by admins for every
// owner, so this page only shows them. Warehouse listings arrive in
// M5, bookings in M8.
// ---------------------------------------------------------------
import { Component, OnInit, inject, signal } from '@angular/core';

import { apiErrorMessage } from '../core/api-error';
import { AuthService } from '../core/auth.service';
import { Setting, SettingValue, SettingsService } from '../core/settings.service';
import { GrainLoader } from '../shared/grain-loader/grain-loader';

@Component({
  selector: 'app-owner-home',
  imports: [GrainLoader],
  templateUrl: './owner-home.html',
  styleUrl: './owner-home.scss',
})
export class OwnerHome implements OnInit {
  private readonly api = inject(SettingsService);
  protected readonly auth = inject(AuthService);

  protected readonly rules = signal<Setting[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal('');

  ngOnInit(): void {
    this.api.list().subscribe({
      next: (rules) => {
        this.rules.set(rules);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(apiErrorMessage(error));
        this.loading.set(false);
      },
    });
  }

  /** Friendly text for a value: true -> "Yes", false -> "No". */
  protected display(value: SettingValue): string {
    if (value === true) return 'Yes';
    if (value === false) return 'No';
    return String(value);
  }
}
