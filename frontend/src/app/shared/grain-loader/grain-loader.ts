// ---------------------------------------------------------------
// GrainLoader: bhandaran.ai's loading spinner.
// A ring of tiny grains - wheat, moong, masoor dal and kala chana -
// that light up one
// after another while the ring slowly turns, like grain being
// poured into a godown.
//
// Usage:
//   <app-grain-loader />                       default 40px, "Loading"
//   <app-grain-loader [size]="24" label="Checking API" />
//
// Screen readers hear the label; the drawing itself is decorative.
// People who turn on "reduce motion" see a still ring.
// ---------------------------------------------------------------
import { Component, input } from '@angular/core';

type GrainKind = 'wheat' | 'moong' | 'dal' | 'chana';

interface Grain {
  angle: number; // position around the ring, in degrees
  kind: GrainKind;
  delay: string; // when this grain lights up in the cycle
}

const GRAIN_COUNT = 12;
const KINDS: GrainKind[] = ['wheat', 'moong', 'dal', 'chana'];
const CYCLE_SECONDS = 1.2; // must match the animation in grain-loader.scss

// Built once: 12 grains, evenly spaced, the 4 kinds repeating (3 each).
// Negative delays start every grain mid-cycle, so the "wave" is
// visible from the very first frame.
const GRAINS: Grain[] = Array.from({ length: GRAIN_COUNT }, (_, i) => ({
  angle: (360 / GRAIN_COUNT) * i,
  kind: KINDS[i % KINDS.length],
  delay: `${(-(GRAIN_COUNT - i) * CYCLE_SECONDS) / GRAIN_COUNT}s`,
}));

@Component({
  selector: 'app-grain-loader',
  templateUrl: './grain-loader.html',
  styleUrl: './grain-loader.scss',
})
export class GrainLoader {
  /** Width and height in pixels. */
  readonly size = input(40);
  /** What is loading, for screen readers. */
  readonly label = input('Loading');

  protected readonly grains = GRAINS;
}
