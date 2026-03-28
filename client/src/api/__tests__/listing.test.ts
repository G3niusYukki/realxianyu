import { describe, it, expect, vi } from "vitest";
import { getTemplates, getBrandAssets, getPublishQueue } from "../listing";
import { api } from "../index";

vi.mock("../index", () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));

describe("listing API", () => {
  it("calls GET /listing/templates for getTemplates", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: {} });
    await getTemplates();
    expect(api.get).toHaveBeenCalledWith("/listing/templates");
  });

  it("calls GET /brand-assets for getBrandAssets", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { ok: true, assets: [] } });
    await getBrandAssets();
    expect(api.get).toHaveBeenCalledWith("/brand-assets", { params: {} });
  });

  it("calls GET /publish-queue for getPublishQueue", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { ok: true, items: [] } });
    await getPublishQueue();
    expect(api.get).toHaveBeenCalledWith("/publish-queue", { params: {} });
  });
});
