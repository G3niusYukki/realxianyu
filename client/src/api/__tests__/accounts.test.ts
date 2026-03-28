import { describe, it, expect, vi } from "vitest";
import { getAccounts } from "../accounts";
import { api } from "../index";

vi.mock("../index", () => ({
  api: { get: vi.fn() },
}));

describe("accounts API", () => {
  it("calls GET /accounts", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { ok: true, data: [] } });
    await getAccounts();
    expect(api.get).toHaveBeenCalledWith("/accounts");
  });
});
