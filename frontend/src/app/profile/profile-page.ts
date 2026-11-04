// ---------------------------------------------------------------
// My profile (M4): name, city and optional GST number. Every role
// (owner, renter, admin) can edit their own.
// ---------------------------------------------------------------
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { apiErrorMessage } from '../core/api-error';
import { AuthService } from '../core/auth.service';
import { City, MasterDataService } from '../core/master-data.service';
import { Profile, ProfileService } from '../core/profile.service';
import { Combobox, optionsFrom } from '../shared/combobox/combobox';
import { GrainLoader } from '../shared/grain-loader/grain-loader';
import { Icon } from '../shared/icon/icon';

@Component({
  selector: 'app-profile-page',
  imports: [FormsModule, GrainLoader, Combobox, Icon],
  templateUrl: './profile-page.html',
  styleUrl: './profile-page.scss',
})
export class ProfilePage implements OnInit {
  private readonly profiles = inject(ProfileService);
  private readonly master = inject(MasterDataService);
  private readonly auth = inject(AuthService);

  protected readonly loading = signal(true);
  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly notice = signal('');
  protected readonly cities = signal<City[]>([]);
  protected readonly cityOptions = computed(() => optionsFrom(this.cities()));
  protected readonly profile = signal<Profile | null>(null);

  protected name = '';
  protected cityId = '';
  protected gst = '';

  ngOnInit(): void {
    this.master.listCities().subscribe((cities) => this.cities.set(cities));
    this.profiles.me().subscribe({
      next: (profile) => {
        this.show(profile);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(apiErrorMessage(error));
        this.loading.set(false);
      },
    });
  }

  protected save(): void {
    this.busy.set(true);
    this.error.set('');
    this.notice.set('');
    this.profiles
      .update({
        name: this.name.trim(),
        city_id: this.cityId || null,
        gst_number: this.gst.trim() || null,
      })
      .subscribe({
        next: (profile) => {
          this.busy.set(false);
          this.show(profile);
          // Keep the name in the header in step with the saved profile.
          const current = this.auth.user();
          if (current) {
            this.auth.user.set({ ...current, name: profile.name });
          }
          this.notice.set('Profile saved.');
        },
        error: (error) => {
          this.busy.set(false);
          this.error.set(apiErrorMessage(error));
        },
      });
  }

  /** Copy the server's values into the form. */
  private show(profile: Profile): void {
    this.profile.set(profile);
    this.name = profile.name ?? '';
    this.cityId = profile.city_id ?? '';
    this.gst = profile.gst_number ?? '';
  }
}
