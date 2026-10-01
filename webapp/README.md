# webapp/ — App web thu thập hồ sơ (React + Vite, PWA)

App cho nhân viên tuyển sinh: quét QR căn cước, chụp ảnh chân dung, gửi hồ sơ lên VPS.
Xem TDD §2.1–§2.4. Build static → nginx VPS phục vụ (`deploy/nginx.conf`).

> Task 13 mới dựng **khung**: scaffold Vite + token Tailwind + font tiếng Việt + `AppLayout`
> (mobile bottom-nav / desktop sidebar) + route placeholder. Màn thật thêm sau:
> đăng nhập (task 17), quét QR (task 18), nhập tay + gửi (task 19).

## Cấu trúc

```
webapp/
├── src/
│   ├── main.tsx · App.tsx        BrowserRouter + route /quet /da-gui /tai-khoan (placeholder)
│   ├── index.css                 @tailwind + token + font Be Vietnam Pro + .field-*
│   ├── components/
│   │   ├── AppLayout.tsx         shell mobile (header + bottom-nav) / desktop (sidebar)
│   │   └── Icon.tsx              icon SVG inline
│   └── pages/Placeholder.tsx     màn tạm "đang dựng"
├── public/icon.svg               icon PWA
├── vite.config.ts                React + vite-plugin-pwa (manifest + service worker)
└── tailwind.config.js            token đồng bộ ui-demo
```

## Chạy

```bash
cd webapp
pnpm install        # hoặc npm install
pnpm dev            # cổng 3022
pnpm build          # tsc -b && vite build → dist/ (nginx VPS phục vụ)
```
