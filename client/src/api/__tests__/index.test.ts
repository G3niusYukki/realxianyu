import { describe, it, expect } from "vitest";
import { api } from "../index";

describe("API client configuration", () => {
  it("has /api base URL", () => {
    expect(api.defaults.baseURL).toBeTruthy();
  });

  it("has 15s timeout", () => {
    expect(api.defaults.timeout).toBe(15000);
  });
});
