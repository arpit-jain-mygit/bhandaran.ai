// ---------------------------------------------------------------
// Welcome banner shown at the top of the owner and renter screens:
// a greeting, a short line about what they can do, and one main
// button. The background uses the grain colour tokens.
//
// Usage:
//   <app-welcome-banner name="Kesar" role="Godown owner"
//     message="..." actionLabel="Add a godown" actionLink="/owner/warehouses/new" />
// ---------------------------------------------------------------
import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-welcome-banner',
  imports: [RouterLink],
  templateUrl: './welcome-banner.html',
  styleUrl: './welcome-banner.scss',
})
export class WelcomeBanner {
  readonly name = input<string | null | undefined>('');
  readonly role = input('');
  readonly message = input('');
  readonly actionLabel = input('');
  readonly actionLink = input('');
}
