// ---------------------------------------------------------------
// Admin > Platform settings (M2).
//
// 1. Platform values: what applies to everyone unless an owner has
//    their own value. "Reset" goes back to the built-in default.
// 2. An owner's own values: owners change these on their own screen;
//    here an admin can look them up or change them by owner ID.
// ---------------------------------------------------------------
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';

import { apiErrorMessage } from '../../core/api-error';
import {
  EffectiveSetting,
  Setting,
  SettingSource,
  SettingValue,
  SettingsService,
} from '../../core/settings.service';
import { ComboOption, Combobox } from '../../shared/combobox/combobox';
import { GrainLoader } from '../../shared/grain-loader/grain-loader';
import { AdminHeader } from '../admin-header/admin-header';

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

@Component({
  selector: 'app-settings-admin',
  imports: [FormsModule, GrainLoader, AdminHeader, Combobox],
  templateUrl: './settings-admin.html',
  styleUrl: './settings-admin.scss',
})
export class SettingsAdmin implements OnInit {
  private readonly api = inject(SettingsService);

  protected readonly settings = signal<Setting[]>([]);
  /** True when at least one rule can be changed per owner. */
  protected anyOverridable(): boolean {
    return this.settings().some((setting) => setting.owner_can_override);
  }
  protected readonly loading = signal(true);
  protected readonly error = signal('');
  protected readonly notice = signal('');

  // Edited values, by setting key, before "Save" is pressed.
  protected draft: Record<string, SettingValue> = {};

  // ---------- owner overrides ----------
  protected ownerIdInput = '';
  protected readonly ownerId = signal('');
  protected readonly ownerSettings = signal<EffectiveSetting[]>([]);
  protected ownerDraft: Record<string, SettingValue> = {};

  ngOnInit(): void {
    this.api.list().subscribe({
      next: (settings) => {
        this.showPlatform(settings);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(apiErrorMessage(error));
        this.loading.set(false);
      },
    });
  }

  // ---------- platform values ----------

  protected savePlatform(setting: Setting): void {
    this.write(
      this.api.setPlatform(setting.key, this.draft[setting.key]),
      `Saved "${setting.label}".`,
      (settings) => this.showPlatform(settings as Setting[]),
    );
  }

  protected resetPlatform(setting: Setting): void {
    this.write(
      this.api.resetPlatform(setting.key),
      `"${setting.label}" is back to its default.`,
      (settings) => this.showPlatform(settings as Setting[]),
    );
  }

  /** True when the edited value differs from what is saved. */
  protected changed(setting: Setting): boolean {
    return this.draft[setting.key] !== setting.value;
  }

  // ---------- owner overrides ----------

  protected newTestOwner(): void {
    this.ownerIdInput = crypto.randomUUID();
    this.loadOwner();
  }

  protected loadOwner(): void {
    const id = this.ownerIdInput.trim();
    this.clearMessages();
    if (!UUID_PATTERN.test(id)) {
      this.error.set('Owner ID must be a UUID, e.g. 3f2b...-....');
      return;
    }
    this.api.forOwner(id).subscribe({
      next: (rows) => {
        this.ownerId.set(id);
        this.showOwner(rows);
      },
      error: (error) => this.error.set(apiErrorMessage(error)),
    });
  }

  protected saveOwner(row: EffectiveSetting): void {
    this.write(
      this.api.setOwner(this.ownerId(), row.key, this.ownerDraft[row.key]),
      `Owner value saved for "${row.label}".`,
      (rows) => this.showOwner(rows as EffectiveSetting[]),
    );
  }

  protected resetOwner(row: EffectiveSetting): void {
    this.write(
      this.api.resetOwner(this.ownerId(), row.key),
      `Owner value removed for "${row.label}".`,
      (rows) => this.showOwner(rows as EffectiveSetting[]),
    );
  }

  // ---------- shared helpers ----------

  /** The setting's rules (type, choices, limits), looked up by key. */
  protected rules(key: string): Setting | undefined {
    return this.settings().find((setting) => setting.key === key);
  }

  /** Friendly text for a value: true -> "Yes", false -> "No". */
  protected show(value: SettingValue): string {
    if (value === true) return 'Yes';
    if (value === false) return 'No';
    return String(value);
  }

  protected sourceLabel(source: SettingSource): string {
    return { owner: 'Owner', platform: 'Platform', default: 'Default' }[source];
  }

  private showPlatform(settings: Setting[]): void {
    this.settings.set(settings);
    this.draft = Object.fromEntries(settings.map((s) => [s.key, s.value]));
    // Platform changes can change an owner's effective values too.
    if (this.ownerId()) {
      this.api.forOwner(this.ownerId()).subscribe((rows) => this.showOwner(rows));
    }
  }

  private showOwner(rows: EffectiveSetting[]): void {
    this.ownerSettings.set(rows);
    this.ownerDraft = Object.fromEntries(rows.map((r) => [r.key, r.value]));
  }

  private write(
    request: Observable<unknown>,
    successMessage: string,
    apply: (result: unknown) => void,
  ): void {
    this.clearMessages();
    request.subscribe({
      next: (result) => {
        apply(result);
        this.notice.set(successMessage);
      },
      error: (error) => this.error.set(apiErrorMessage(error)),
    });
  }

  private clearMessages(): void {
    this.error.set('');
    this.notice.set('');
  }

  /** A setting's choices as type-or-select options. */
  protected choiceOptions(choices: readonly string[] | undefined): ComboOption[] {
    return (choices ?? []).map((choice) => ({ value: choice, label: choice }));
  }
}
