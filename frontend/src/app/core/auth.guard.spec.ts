// ---------------------------------------------------------------
// Tests for roleGuard: who gets into which page.
// The AuthService is faked so no HTTP call happens.
// ---------------------------------------------------------------
import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  Router,
  RouterStateSnapshot,
  UrlTree,
  provideRouter,
} from '@angular/router';
import { Observable, firstValueFrom, of } from 'rxjs';

import { AuthService, Role, User } from './auth.service';
import { roleGuard } from './auth.guard';

function fakeAuth(user: User | null) {
  return {
    ensureLoaded: (): Observable<User | null> => of(user),
    homeFor: (u: User) => (u.roles.includes('ADMIN') ? '/admin/master-data' : '/owner'),
  };
}

function userWith(...roles: Role[]): User {
  return { id: 'u1', phone: '+919000000001', name: 'Test', roles };
}

// Run the guard in Angular's injection context and wait for its answer.
async function runGuard(roles: Role[], user: User | null, url: string): Promise<boolean | UrlTree> {
  TestBed.configureTestingModule({
    providers: [provideRouter([]), { provide: AuthService, useValue: fakeAuth(user) }],
  });
  const guard = roleGuard(...roles);
  const result = TestBed.runInInjectionContext(() =>
    guard({} as ActivatedRouteSnapshot, { url } as RouterStateSnapshot),
  );
  return firstValueFrom(result as Observable<boolean | UrlTree>);
}

describe('roleGuard', () => {
  it('lets a user with the role through', async () => {
    expect(await runGuard(['ADMIN'], userWith('ADMIN'), '/admin/settings')).toBe(true);
  });

  it('sends a logged-out visitor to login with the wanted page', async () => {
    const result = (await runGuard(['ADMIN'], null, '/admin/settings')) as UrlTree;
    const router = TestBed.inject(Router);
    expect(router.serializeUrl(result)).toBe('/login?next=%2Fadmin%2Fsettings');
  });

  it('sends a user without the role to their own main screen', async () => {
    const result = (await runGuard(['ADMIN'], userWith('OWNER'), '/admin/settings')) as UrlTree;
    const router = TestBed.inject(Router);
    expect(router.serializeUrl(result)).toBe('/owner');
  });
});
