"use client"

import { useState, useEffect } from "react"
import { TrendingUp, Disc3, ArrowLeft, MessageCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { VinylCard } from "@/components/vinyl-card"
import Link from "next/link"

const API_URL = "http://176.98.178.109:8000/api/records"

type VinylRecord = {
  id: string
  article_id?: string
  title: string
  artist: string
  year: number
  country: string
  price: number
  status: "available" | "reserved" | "sold" | "preorder"
  image: string
  photo_url?: string
  genre?: string
  label?: string
  condition?: string
  description?: string
  preorder_count?: number
}

export default function UpcomingPage() {
  const [records, setRecords] = useState<VinylRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchRecords() {
      try {
        const response = await fetch(API_URL, {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()

        if (data && data.records && Array.isArray(data.records)) {
          const formattedRecords = data.records.map((r: any) => ({
            id: r.article_id || r.id || String(Math.random()),
            article_id: r.article_id,
            title: r.title,
            artist: r.artist,
            year: r.year,
            country: r.country || "Россия",
            price: r.price,
            status:
              r.status === "🟢 Доступна" || r.status === "available"
                ? "available"
                : r.status === "🟡 Предзаказ" || r.status === "preorder"
                  ? "preorder"
                  : r.status === "🔴 Продана" || r.status === "sold"
                    ? "sold"
                    : "available",
            image: r.photo_url || r.image || "/placeholder.svg",
            photo_url: r.photo_url,
            genre: r.genre,
            label: r.label,
            condition: r.condition,
            description: r.description,
            preorder_count: Math.floor(Math.random() * 20),
          }))

          setRecords(formattedRecords)
        }
        setLoading(false)
      } catch (error) {
        console.error("Ошибка загрузки:", error)
        setLoading(false)
      }
    }

    fetchRecords()
    const interval = setInterval(fetchRecords, 120000)
    return () => clearInterval(interval)
  }, [])

  // Фильтруем только зарезервированные пластинки и предзаказы
  const upcomingRecords = records.filter((r) => r.status === "reserved" || r.status === "preorder")

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <Link href="/">
              <Button variant="ghost" size="sm" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Назад
              </Button>
            </Link>
            
            <Link href="/" className="flex items-center gap-2">
              <div className="flex items-center gap-0.5">
                <Disc3 className="h-6 w-6 sm:h-7 sm:w-7 text-primary" />
                <Disc3 className="h-6 w-6 sm:h-7 sm:w-7 text-primary -ml-3 opacity-50" />
              </div>
              <span className="text-base sm:text-lg font-bold text-primary">BALT-SET</span>
            </Link>

            <a
              href="https://t.me/YOUR_ADMIN_USERNAME"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="ghost" size="icon" className="rounded-full">
                <MessageCircle className="h-5 w-5 text-primary" />
              </Button>
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative bg-gradient-to-b from-primary/5 to-white py-12 sm:py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full text-primary text-sm font-medium">
              <TrendingUp className="h-4 w-4" />
              Актуальные поставки
            </div>
            
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-foreground">
              Ближайшие поставки
            </h1>
            <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
              Зарезервированные пластинки и популярные предзаказы, которые скоро появятся в наличии
            </p>
          </div>
        </div>
      </section>

      {/* Records Grid */}
      <section className="py-8">
        <div className="container mx-auto px-4">
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="mt-4 text-muted-foreground">Загрузка...</p>
            </div>
          ) : upcomingRecords.length > 0 ? (
            <>
              <div className="mb-6 flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  Найдено: {upcomingRecords.length} {upcomingRecords.length === 1 ? "пластинка" : "пластинок"}
                </p>
              </div>
              
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                {upcomingRecords.map((record) => (
                  <VinylCard key={record.id} record={record} />
                ))}
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Пока нет ближайших поставок</h3>
              <p className="text-muted-foreground mb-6">
                В данный момент все пластинки либо в наличии, либо уже проданы
              </p>
              <Link href="/">
                <Button>
                  Вернуться на главную
                </Button>
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 bg-gradient-to-r from-primary/5 via-purple-500/5 to-primary/5">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto text-center space-y-6">
            <h2 className="text-2xl sm:text-3xl font-bold text-foreground">
              Не нашли нужную пластинку?
            </h2>
            <p className="text-muted-foreground">
              Свяжитесь с нами в Telegram, и мы поможем найти любой винил!
            </p>
            <a
              href="https://t.me/YOUR_ADMIN_USERNAME"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button size="lg" className="gap-2">
                <MessageCircle className="h-5 w-5" />
                Написать в Telegram
              </Button>
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}
