import { notFound } from "next/navigation"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Disc3 } from "lucide-react"
import Link from "next/link"

const API_URL = "http://176.98.178.109:8000"

// Генерация статических параметров для всех пластинок
export async function generateStaticParams() {
  try {
    const res = await fetch(`${API_URL}/api/records`, { next: { revalidate: 3600 } })
    const data = await res.json()

    return data.records.map((record: any) => ({
      id: record.article_id || record.id,
    }))
  } catch (error) {
    console.error("Ошибка загрузки списка пластинок:", error)
    return []
  }
}

// Генерация метаданных для SEO
export async function generateMetadata({ params }: { params: { id: string } }) {
  try {
    const res = await fetch(`${API_URL}/api/records/${params.id}`, { next: { revalidate: 3600 } })
    const record = await res.json()

    return {
      title: `${record.title} - ${record.artist} | BALT-SET`,
      description:
        record.description ||
        `Купить виниловую пластинку ${record.title} от ${record.artist} (${record.year}) в Калининграде`,
    }
  } catch {
    return {
      title: "Пластинка не найдена | BALT-SET",
    }
  }
}

export default async function VinylPage({ params }: { params: { id: string } }) {
  let record

  try {
    const res = await fetch(`${API_URL}/api/records/${params.id}`, {
      next: { revalidate: 60 },
      cache: "force-cache",
    })

    if (!res.ok) {
      notFound()
    }

    record = await res.json()
  } catch (error) {
    console.error("Ошибка загрузки пластинки:", error)
    notFound()
  }

  // Преобразуем статус
  const statusMap: Record<string, string> = {
    "🟢 Доступна": "available",
    "🟡 Предзаказ": "preorder",
    "🔴 Продана": "sold",
  }

  const status = statusMap[record.status] || "available"

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Назад
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-0.5">
                <Disc3 className="h-6 w-6 text-primary" />
                <Disc3 className="h-6 w-6 text-primary -ml-3 opacity-50" />
              </div>
              <h1 className="text-lg font-bold text-primary">BALT-SET</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="container mx-auto px-4 py-8 sm:py-12">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-8 md:gap-12">
            {/* Image */}
            <div className="relative aspect-square rounded-2xl overflow-hidden bg-muted shadow-2xl">
              <Image
                src={record.photo_url || record.image || "/placeholder.svg"}
                alt={record.title}
                fill
                className="object-cover"
                priority
              />
            </div>

            {/* Details */}
            <div className="space-y-6">
              <div>
                <h1 className="text-3xl sm:text-4xl font-bold text-foreground mb-2 text-balance">{record.title}</h1>
                <p className="text-xl sm:text-2xl text-muted-foreground mb-4">{record.artist}</p>

                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary" className="text-sm px-3 py-1">
                    {record.genre || "Рок"}
                  </Badge>
                  <Badge variant="outline" className="text-sm px-3 py-1">
                    {record.year}
                  </Badge>
                  <Badge
                    variant={status === "available" ? "default" : status === "preorder" ? "secondary" : "destructive"}
                    className="text-sm px-3 py-1"
                  >
                    {status === "available" ? "В наличии" : status === "preorder" ? "Предзаказ" : "Продано"}
                  </Badge>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 p-6 bg-muted/30 rounded-xl">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Лейбл</p>
                  <p className="font-semibold text-foreground">{record.label || "—"}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Страна</p>
                  <p className="font-semibold text-foreground">{record.country || "—"}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Состояние</p>
                  <p className="font-semibold text-foreground">{record.condition || "—"}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Цена</p>
                  <p className="text-2xl font-bold text-primary">{record.price?.toLocaleString("ru-RU")} ₽</p>
                </div>
              </div>

              {/* AI Description */}
              {record.description && (
                <div className="p-6 bg-gradient-to-br from-primary/5 to-purple-500/5 rounded-xl border border-primary/20">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold">
                      AI
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">AI-музыковед</p>
                      <p className="text-xs text-muted-foreground">Экспертное описание</p>
                    </div>
                  </div>
                  <p className="text-sm leading-relaxed text-foreground/90">{record.description}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="space-y-3">
                {status === "preorder" && (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-4">
                    <p className="text-sm text-blue-900 mb-2 font-medium">
                      Вы можете уточнить детали предзаказа (лейбл, год, состояние)
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-blue-600 border-blue-300 hover:bg-blue-100 bg-transparent"
                    >
                      Редактировать запрос
                    </Button>
                  </div>
                )}

                <Button
                  size="lg"
                  className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-base h-12"
                  disabled={status === "sold"}
                >
                  {status === "sold" ? "Продано" : status === "preorder" ? "Оформить предзаказ" : "Купить сейчас"}
                </Button>

                {status !== "sold" && (
                  <Button size="lg" variant="outline" className="w-full font-semibold text-base h-12 bg-transparent">
                    Уведомить о поступлении
                  </Button>
                )}
              </div>

              <div className="text-center pt-4 text-sm text-muted-foreground">
                <p>
                  📞 Вопросы? Звоните: <span className="font-semibold text-foreground">+7 (4012) 52-07-25</span>
                </p>
                <p className="mt-1">Пн-Сб: 10:00-19:00 • Калининград</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
