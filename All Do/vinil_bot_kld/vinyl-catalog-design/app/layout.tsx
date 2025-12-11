import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ subsets: ["latin", "cyrillic"] })

export const metadata: Metadata = {
  title: "BALT-SET | Виниловые пластинки бесплатный предзаказ в Калининграде",
  description: "Найдём любую пластинку и привезём из Москвы. Виниловые пластинки с доставкой в Калининград.",
  keywords: ["винил", "виниловые пластинки", "Калининград", "музыка", "предзаказ", "balt-set"],
  openGraph: {
    title: "BALT-SET | Виниловые пластинки бесплатный предзаказ",
    description: "Найдём любую пластинку и привезём из Москвы",
    url: "https://balt-set.ru",
    siteName: "BALT-SET",
    locale: "ru_RU",
    type: "website",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ru">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
