// ---------------------------------------------------------------
// Owner's main screen (M3). For now: the owner's own booking rules
// (platform settings they may change for their godowns). Warehouse
// listings arrive in M5, bookings in M8.
// ---------------------------------------------------------------
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Observable, forkJoin } from 'rxjs';

import { apiErrorMessage } from '../core/api-error';
import { AuthService } from '../core/auth.service';
import { EffectiveSetting, Setting, SettingValue, SettingsService } from '../core/settings.service';
import { GrainLoader } from '../shared/grain-loader/grain-loader';

@Component({
  selector: 'app-owner-home',
  imports: [FormsModule, GrainLoader],
  templateUrl: './owner-home.html',
  styleUrl: './owner-home.scss',
})
export class OwnerHome implements OnInit {
  private readonly api = inject(SettingsService);
  protected readonly auth = inject(AuthService);

  // Rules (type, choices, platform value) and what applies to me.
  protected readonly rules = signal<Setting[]>([]);
  protected readonly mine = signal<EffectiveSetting[]>([]);
  protected draft: Record<string, SettingValue> = {};

  protected readonly loading = signal(true);
  protected readonly error = signal('');
  protected readonly notice = signal('');

  ngOnInit(): void {
    forkJoin({ rules: this.api.list(), mine: this.api.mine() }).subscribe({
      next: ({ rules, mine }) => {
        this.rules.set(rules);
        this.apply(mine);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(apiErrorMessage(error));
        this.loading.set(false);
      },
    });
  }

  protected ruleFor(key: string): Setting | undefined {
    return this.rules().find((rule) => rule.key === key);
  }

  protected save(row: EffectiveSetting): void {
    this.write(this.api.setMine(row.key, this.draft[row.key]), `Saved "${row.label}".`);
  }

  protected usePlatform(row: EffectiveSetting): void {
    this.write(this.api.resetMine(row.key), `"${row.label}" now follows the platform default.`);
  }

  protected changed(row: EffectiveSetting): boolean {
    return this.draft[row.key] !== row.value;
  }

  /** Friendly text for a value: true -> "Yes", false -> "No". */
  protected display(value: SettingValue): string {
    if (value === true) return 'Yes';
    if (value === false) return 'No';
    return String(value);
  }

  /** Show fresh values from the server and reset the editors to them. */
  private apply(rows: EffectiveSetting[]): void {
    this.mine.set(rows);
    this.draft = Object.fromEntries(rows.map((row) => [row.key, row.value]));
  }

  private write(request: Observable<EffectiveSetting[]>, message: string): void {
    this.error.set('');
    this.notice.set('');
    request.subscribe({
      next: (rows) => {
        this.apply(rows);
        this.notice.set(message);
      },
      error: (error) => this.error.set(apiErrorMessage(error)),
    });
  }
}
