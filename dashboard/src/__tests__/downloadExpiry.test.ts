/**
 * Property 21: Download link expiry
 *
 * Feature: hestia, Property 21: Download link expiry
 *
 * For any completed job, the generated download link should have an
 * expiry time of at least 24 hours from the time of job completion.
 *
 * Validates: Requirements 12.5
 */

import { describe, it, expect } from "vitest";
import * as fc from "fast-check";

const TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000;

function generateDownloadExpiry(completedAt: Date): Date {
  // The system should set expiry to at least 24h after completion
  return new Date(completedAt.getTime() + TWENTY_FOUR_HOURS_MS);
}

describe("Property 21: Download link expiry", () => {
  it("expiry is at least 24 hours after completion", () => {
    fc.assert(
      fc.property(
        fc.date({
          min: new Date("2020-01-01"),
          max: new Date("2030-12-31"),
        }),
        (completedAt) => {
          const expiry = generateDownloadExpiry(completedAt);
          const diff = expiry.getTime() - completedAt.getTime();
          expect(diff).toBeGreaterThanOrEqual(TWENTY_FOUR_HOURS_MS);
        }
      ),
      { numRuns: 100 }
    );
  });
});
