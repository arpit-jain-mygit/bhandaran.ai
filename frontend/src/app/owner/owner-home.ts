// ---------------------------------------------------------------
// Owner's main screen (M3). A placeholder for now: listings arrive in
// M5 and bookings in M8. Booking rules are set by admins, not here.
// ---------------------------------------------------------------
import { Component, inject } from '@angular/core';

import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-owner-home',
  templateUrl: './owner-home.html',
  styleUrl: './owner-home.scss',
})
export class OwnerHome {
  protected readonly auth = inject(AuthService);
}
