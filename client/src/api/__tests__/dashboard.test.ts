import { describe, it, expect, vi } from "vitest";
import { getSystemStatus, getDashboardSummary, getUnmatchedStats, serviceControl } from "../dashboard";
import { api } from "../index";

vi.mock("../index", () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));

describe("dashboard API", () => {
  it("calls GET /status for getSystemStatus", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: {} });
    await getSystemStatus();
    expect(api.get).toHaveBeenCalledWith("/status");
  });

  it("calls GET /summary for getDashboardSummary", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { data: {} } });
    await getDashboardSummary();
    expect(api.get).toHaveBeenCalledWith("/summary");
  });

  it("calls POST /service/control for serviceControl", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: {} });
    await serviceControl("start");
    expect(api.post).toHaveBeenCalledWith("/service/control", { action: "start" });
  });

  it("calls GET /unmatched-stats for getUnmatchedStats", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { ok: true, total_count: 1, top_keywords: [], daily_counts: [] } });
    const res = await getUnmatchedStats();
    expect(api.get).toHaveBeenCalledWith("/unmatched-stats");
    expect(res.data.ok).toBe(true);
  });

  it("rejects when getUnmatchedStats request fails", async () => {
    vi.mocked(api.get).mockRejectedValue(new Error("network down"));
    await expect(getUnmatchedStats()).rejects.toThrow("network down");
  });
});
