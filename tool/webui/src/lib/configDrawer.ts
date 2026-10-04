import { createContext, useContext } from "react";

// Bảng Cấu hình kết nối dùng chung cả tool (HTG-07): mở từ icon ⚙ trên header.
// ToolLayout giữ trạng thái + render drawer; màn con (đăng nhập, lối tắt "chưa
// khai CSDL đích"…) gọi open() qua context này để mở bảng mà khỏi điều hướng.
export interface ConfigDrawerCtx {
  open: () => void;
}

export const ConfigDrawerContext = createContext<ConfigDrawerCtx>({ open: () => {} });

export const useConfigDrawer = () => useContext(ConfigDrawerContext);
