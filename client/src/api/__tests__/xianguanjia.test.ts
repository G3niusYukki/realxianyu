import { describe, it, expect, vi } from "vitest";
import { getProducts, getOrders } from "../xianguanjia";
import { api } from "../index";

vi.mock("../index", () => ({
  api: { post: vi.fn() },
}));

describe("xianguanjia API", () => {
  it("calls proxyXgjApi for getProducts", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { ok: true, data: {} } });
    await getProducts(1, 10);
    expect(api.post).toHaveBeenCalledWith("/xgj/proxy", {
      apiPath: "/api/open/product/list",
      payload: { page_no: 1, page_size: 10 },
    });
  });

  it("calls proxyXgjApi for getOrders", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { ok: true, data: {} } });
    await getOrders({ page_no: 1 });
    expect(api.post).toHaveBeenCalledWith("/xgj/proxy", {
      apiPath: "/api/open/order/list",
      payload: { page_no: 1 },
    });
  });
});
