// ---------------------------------------------------------------
// Renter's main screen (M3). Bookings and stock arrive in M8/M10;
// for now a welcome and a link to search for space.
// ---------------------------------------------------------------
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../core/auth.service';
import { WelcomeBanner } from '../shared/welcome-banner/welcome-banner';

@Component({
  selector: 'app-renter-home',
  imports: [RouterLink, WelcomeBanner],
  templateUrl: './renter-home.html',
  styleUrl: './renter-home.scss',
})
export class RenterHome {
  protected readonly auth = inject(AuthService);
}
