import { describe, it, expect, vi } from "vitest";
import { getSystemConfig, saveSystemConfig, getConfigSections } from "../config";
import { api } from "../index";

vi.mock("../index", () => ({
  api: { get: vi.fn(), put: vi.fn() },
}));

describe("config API", () => {
  it("calls GET /config for getSystemConfig", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { config: {} } });
    await getSystemConfig();
    expect(api.get).toHaveBeenCalledWith("/config");
  });

  it("calls PUT /config for saveSystemConfig", async () => {
    vi.mocked(api.put).mockResolvedValue({ data: { config: {} } });
    await saveSystemConfig({ key: "val" });
    expect(api.put).toHaveBeenCalledWith("/config", { key: "val" });
  });

  it("calls GET /config/sections for getConfigSections", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { sections: [] } });
    await getConfigSections();
    expect(api.get).toHaveBeenCalledWith("/config/sections");
  });
});
