<!-- claudemd:start — khối này do lệnh /claudemd sinh, chạy lại sẽ ghi đè nguyên khối.
     Muốn thêm ghi chú riêng thì viết ngoài cặp marker. -->

# Tài liệu dự án

> Đường dẫn dưới đây ghi trần, **không dùng cú pháp `@file`** — dấu `@` khiến toàn bộ file bị nạp vào context ngay từ đầu mỗi phiên, tốn context và chậm. Đọc file khi việc đang làm thực sự cần tới.

- PRD — yêu cầu sản phẩm, trạng thái từng story: `docs/PRD.md`
- TDD — thiết kế kỹ thuật: `docs/TDD.md`
- Quyết định kỹ thuật — vì sao chọn, đánh đổi gì: `docs/TDD-decisions.md`
- Kế hoạch build — thứ tự code, phase, checkpoint: `docs/BUILD-PLAN.md`
- Tài liệu nghiệp vụ (BA): `docs/ba/`
- Mục lục prototype — màn nào đã dựng, màn nào còn placeholder: `ui-demo/SCREENS.md`
- **Tham chiếu DB đích GPLX_CDB_CSDT** (cách tạo HV/sinh mã/FK cascade/cột kết quả đào tạo) — **đọc trước khi code bất cứ phần nào ghi vào GPLX_CDB_CSDT** (Sync + module Kết quả đào tạo): `docs/DB-GPLX_CDB_CSDT.md`

# Cấu trúc code

- **Code thật:**
  - `tool/` — tool nạp DB tại máy CSDT: `tool/app/` (FastAPI localhost, cổng 8000) + `tool/webui/` (React + Vite, cổng 3011). Chạy/test: xem `tool/README.md`.
  - `server/` — backend VPS (FastAPI + PostgreSQL), khung dựng ở task 12, auth JWT + 3 vai trò ở task 14: `server/app/` + `server/db/init.sql` + `docker-compose.yml` (api+postgres+nginx). Chạy/test: xem `server/README.md`.
  - `webapp/` — app web PWA (React + Vite), khung dựng ở task 13: `webapp/src/` + `AppLayout` mobile/desktop. Build static → nginx VPS phục vụ. Chạy: `cd webapp && pnpm dev` (cổng 3022).
- **Prototype — KHÔNG sửa khi làm tính năng thật:** `ui-demo/` (project Vite + React riêng, chạy bằng `cd ui-demo && pnpm dev` — cổng 3021). Chỉ là tham chiếu style/layout.

# Nguyên tắc khi implement

- Trước khi code một User Story: đọc story đó trong PRD và phần kỹ thuật liên quan trong TDD
- Implement đầy đủ theo từng tiêu chí "Done khi" trong story
- Tham chiếu TDD cho mọi quyết định kỹ thuật: tech stack, DB schema, API design
- Trong một story, code theo thứ tự phụ thuộc: DB → API → UI. Không đụng sang story khác
- Trước khi viết layout một màn: đọc `ui-demo/SCREENS.md` tra route của màn, rồi mở file màn tương ứng trong `ui-demo/src/pages/` — bám bố cục và component đã có, không tự sáng tạo layout mới
- Gọi tính năng bằng mã ngắn (vd `NAP-05`), không gọi bằng tên — đối chiếu bằng mã thì đúng sai rõ ràng
- Hỏi trước khi làm nếu có gì chưa rõ trong PRD hoặc TDD

# Quy ước trạng thái trong PRD

Ghi ở dòng `**Trạng thái:**` ngay dưới tiêu đề, **cả cấp Feature lẫn cấp Story**:
📝 Draft (chưa chốt xong) · ⏳ Todo · 🔄 In Progress · ⚠️ Partial · ✅ Done

- **Story ✅** = code xong và đã kiểm pass. **Feature ✅** = mọi story con ✅ **và** E2E pass nếu Feature có luồng cần E2E **và** user duyệt chốt — ghi kèm ngày: `✅ Đã chốt — 01/10/2026`
- Bắt đầu code story nào thì đổi story đó sang 🔄, không đổi mục khác
- ✅ chỉ đặt khi đã chạy kiểm và pass. Chưa kiểm được thì để ⚠️ kèm lý do
- ⚠️ bắt buộc ghi rõ phần nào chưa xong, ngay trên cùng dòng đó
- **Không tự chốt ✅ cho Feature.** Đủ story chỉ là điều kiện cần, phải hỏi user
- Đổi trạng thái **chỉ được sửa dòng `**Trạng thái:**`** — không chạm dòng chứa mã
- **Story đang ✅ hoá ra chưa xong → hạ về đâu tuỳ bằng chứng.** Yêu cầu vừa đổi (`/capnhat`) → **⏳ Todo**; test fail (`/kiemthu`) hoặc bug 🔴/🟠 tái hiện được (`/suabug`) → **⚠️ Partial**. Ba ca này là sự thật máy đọc được nên **hạ thẳng, không hỏi**. Riêng `/tieptheo` không tìm thấy commit mang mã story → **không tự hạ, phải hỏi**, vì đó là suy đoán

# Khi user báo việc phát sinh

- **Yêu cầu mới, đổi quy tắc nghiệp vụ, đổi giao diện** → nhắc chạy **`/capnhat`** trước khi code
- **Code không làm đúng yêu cầu đã có trong PRD** → nhắc chạy **`/suabug`**

Phân biệt: PRD **có ghi** hành vi đúng mà code làm khác → bug. PRD **chưa nói gì** → yêu cầu mới.

Sửa thẳng vào code mà không qua hai lệnh này thì PRD, TDD, sổ thay đổi và kế hoạch build lệch nhau — và không cơ chế đối chiếu nào phát hiện được, vì chúng đều so tài liệu với tài liệu.

<!-- claudemd:end -->

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **PMNhapHocVien** (2376 symbols, 4656 relationships, 151 execution flows).

> Index stale? Run `node C:/gnindex/PMCSDTLX/run.cjs analyze --index-only` from the project root — it auto-selects an available runner. No `C:/gnindex/PMCSDTLX/run.cjs` yet? Bootstrap with `npx`, `bunx`, or `pnpm dlx` — e.g. `bunx gitnexus@latest analyze` (npm 11 npx crash; #1939).

## Always Do

- **MUST run impact before editing.** Use `impact({target: "symbolName", direction: "upstream"})` or `node C:/gnindex/PMCSDTLX/run.cjs impact "symbolName" --direction upstream --repo .`; report callers, processes, and risk. Never substitute grep for graph analysis.
- **MUST analyze graph changes before committing.** Use `detect_changes({scope: "all"})` (MCP) or `node C:/gnindex/PMCSDTLX/run.cjs detect-changes --scope all --repo .` (CLI fallback). `partial: true` or `truncated: true` is not a clean check — a zero means unseen, not unaffected; re-run it. For regression review: `detect_changes({scope: "compare", base_ref: "main"})` or `node C:/gnindex/PMCSDTLX/run.cjs detect-changes --scope compare --base-ref "main" --repo .`.
- MUST warn on HIGH/CRITICAL `risk` pre-edit; never use `riskSharedAxes` to waive a HIGH/CRITICAL `risk` warning. Compare File/symbol: MCP File omits axes; Graph-RAG expands File.
- **MUST treat `risk: UNKNOWN` as unresolved, not as low.** An empty caller set is not evidence the symbol is unused — it can also mean the callers are not resolvable by the index (plain-object property access, dynamic dispatch, cross-language calls). `impact` pairs `UNKNOWN` with a `riskNote` saying so. Confirm with a text search before treating the symbol as safe to change or delete; do not proceed on the strength of a zero.
- **MUST use `query({search_query: "concept"})` for concepts/flows, `context({name: "symbolName"})` for a named symbol, or `impact` for blast radius, on read-only callers, dependencies, imports, or execution flow.** Graph first; text search only for empty/`UNKNOWN`/literals.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method before MCP/CLI impact analysis.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis, and never read `UNKNOWN` as an all-clear — it means the walk could not answer, which is the one verdict that requires confirming by other means.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit before MCP/CLI graph change analysis.

## Resources

| Resource | Use for |
| --- | --- |
| `gitnexus://repo/PMNhapHocVien/context` | Codebase overview, check index freshness |
| `gitnexus://repo/PMNhapHocVien/clusters` | All functional areas |
| `gitnexus://repo/PMNhapHocVien/processes` | All execution flows |
| `gitnexus://repo/PMNhapHocVien/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
| --- | --- |
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
