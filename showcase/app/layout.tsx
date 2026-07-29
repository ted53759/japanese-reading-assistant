import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Japanese Reading Assistant | 公開展示版",
  description: "讓初學者透過故事閱讀日文的 AI 閱讀輔助工具展示版。",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-Hant"><body>{children}</body></html>;
}
