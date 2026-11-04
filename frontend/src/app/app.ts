// ---------------------------------------------------------------
// Root component: the app "shell" (header with nav + page area).
// Pages are swapped inside <router-outlet> based on the URL
// (routes are listed in app.routes.ts) - the page never reloads.
// On phones the nav folds into a menu button.
// ---------------------------------------------------------------
import { Component, OnInit, inject, signal } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';

import { AuthService } from './core/auth.service';
import { Icon } from './shared/icon/icon';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Icon],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  /** Phone menu open? Closes itself after each navigation. */
  protected readonly menuOpen = signal(false);
  protected readonly loggingOut = signal(false);

  ngOnInit(): void {
    // Find out once at start-up who is logged in (cookie check).
    this.auth.ensureLoaded().subscribe();
    this.router.events
      .pipe(filter((event) => event instanceof NavigationEnd))
      .subscribe(() => this.menuOpen.set(false));
  }

  protected logout(): void {
    this.loggingOut.set(true);
    this.auth.logout().subscribe(() => {
      this.loggingOut.set(false);
      this.menuOpen.set(false);
      this.router.navigateByUrl('/');
    });
  }
}
