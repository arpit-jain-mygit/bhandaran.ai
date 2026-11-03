// ---------------------------------------------------------------
// Route guard: only let a page open for users with one of the given
// roles. Not logged in -> login page (then back here). Logged in but
// wrong role -> their own main screen.
//
// Usage in app.routes.ts:  canActivate: [roleGuard('ADMIN')]
// (The API checks roles too - this only keeps the screens tidy.)
// ---------------------------------------------------------------
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map } from 'rxjs';

import { AuthService, Role } from './auth.service';

export function roleGuard(...roles: Role[]): CanActivateFn {
  return (_route, state) => {
    const auth = inject(AuthService);
    const router = inject(Router);

    return auth.ensureLoaded().pipe(
      map((user) => {
        if (!user) {
          return router.createUrlTree(['/login'], { queryParams: { next: state.url } });
        }
        if (roles.some((role) => user.roles.includes(role))) {
          return true;
        }
        return router.parseUrl(auth.homeFor(user));
      }),
    );
  };
}
