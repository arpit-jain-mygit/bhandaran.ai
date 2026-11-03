// ---------------------------------------------------------------
// Owner's main screen (M3, M4). Owners invite renters by email here;
// listings arrive in M5 and bookings in M8. Booking rules are set by
// admins, not here.
// ---------------------------------------------------------------
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { apiErrorMessage } from '../core/api-error';
import { AuthService } from '../core/auth.service';
import { ProfileService } from '../core/profile.service';

@Component({
  selector: 'app-owner-home',
  imports: [FormsModule],
  templateUrl: './owner-home.html',
  styleUrl: './owner-home.scss',
})
export class OwnerHome {
  private readonly profiles = inject(ProfileService);
  protected readonly auth = inject(AuthService);

  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly notice = signal('');

  protected renterEmail = '';
  protected renterName = '';

  protected invite(): void {
    this.busy.set(true);
    this.error.set('');
    this.notice.set('');
    this.profiles.inviteRenter(this.renterEmail.trim(), this.renterName.trim()).subscribe({
      next: (renter) => {
        this.busy.set(false);
        this.notice.set(`Invite sent to ${renter.email}. They can log in with that email.`);
        this.renterEmail = '';
        this.renterName = '';
      },
      error: (error) => {
        this.busy.set(false);
        this.error.set(apiErrorMessage(error));
      },
    });
  }
}
