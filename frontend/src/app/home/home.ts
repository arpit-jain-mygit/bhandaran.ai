// ---------------------------------------------------------------
// Home page: a short heading and the "Find storage space" search.
// ---------------------------------------------------------------
import { Component } from '@angular/core';

import { FindSpace } from './find-space/find-space';

@Component({
  selector: 'app-home',
  imports: [FindSpace],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {}
