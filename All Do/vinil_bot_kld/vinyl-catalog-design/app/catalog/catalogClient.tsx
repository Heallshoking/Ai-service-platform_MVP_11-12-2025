"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Disc3 } from "lucide-react"
import { VinylCard } from "@/components/vinyl-card"
import { useState } from "react"

interface Record {
  id: string | number
  article_id?: string | number
  title?: string
  name?: string
  artist?: string
  performer?: string
  year?: number
  country?: string
  price?: number
  status?: string
  photo_url?: string
  image?: string
  genre?: string
  label?: string
  condition?: string
}

interface CatalogClientProps {
  records: Record[]
  categories: string[]
}

export default function CatalogClient({ records, categories }: CatalogClientProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const displayRecords = selectedCategory ? records.filter((record) => record.genre === selectedCategory) : records

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Назад
              </Button>
            </Link>
            <Link href="/" className="flex items-center gap-2">
              <div className="flex items-center gap-0.5">
                <Disc3 className="h-6 w-6 text-primary" />
                <Disc3 className="h-6 w-6 text-primary -ml-3 opacity-50" />
              </div>
              <h1 className="text-lg font-bold text-primary">BALT-SET</h1>
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-foreground mb-6">Все категории</h1>

        <div className="flex flex-wrap gap-2 mb-8">
          <Button
            variant={selectedCategory === null ? "default" : "outline"}
            onClick={() => setSelectedCategory(null)}
            className="rounded-full"
          >
            Все
          </Button>
          {categories.map((category) => (
            <Button
              key={category}
              variant={selectedCategory === category ? "default" : "outline"}
              onClick={() => setSelectedCategory(category)}
              className="rounded-full"
            >
              {category}
            </Button>
          ))}
        </div>

        {selectedCategory === null ? (
          categories.map((category) => {
            const categoryRecords = records.filter((record: Record) => record.genre === category)

            if (categoryRecords.length === 0) return null

            return (
              <div key={category} className="mb-12">
                <h2 className="text-2xl font-bold text-foreground mb-6">{category}</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                  {categoryRecords.map((record: Record) => (
                    <VinylCard
                      key={record.id}
                      record={{
                        id: String(record.article_id || record.id),
                        title: record.title || record.name || "",
                        artist: record.artist || record.performer || "",
                        year: record.year || 2000,
                        country: record.country || "Unknown",
                        price: record.price || 0,
                        status: record.status?.includes("Доступна")
                          ? "available"
                          : record.status?.includes("Предзаказ")
                            ? "preorder"
                            : "sold",
                        image: record.photo_url || record.image || "/placeholder.svg",
                        genre: record.genre,
                        label: record.label,
                        condition: record.condition,
                      }}
                      compact
                    />
                  ))}
                </div>
              </div>
            )
          })
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {displayRecords.map((record: Record) => (
              <VinylCard
                key={record.id}
                record={{
                  id: String(record.article_id || record.id),
                  title: record.title || record.name || "",
                  artist: record.artist || record.performer || "",
                  year: record.year || 2000,
                  country: record.country || "Unknown",
                  price: record.price || 0,
                  status: record.status?.includes("Доступна")
                    ? "available"
                    : record.status?.includes("Предзаказ")
                      ? "preorder"
                      : "sold",
                  image: record.photo_url || record.image || "/placeholder.svg",
                  genre: record.genre,
                  label: record.label,
                  condition: record.condition,
                }}
                compact
              />
            ))}
          </div>
        )}

        {displayRecords.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground text-lg">В этой категории пока нет пластинок</p>
          </div>
        )}
      </main>
    </div>
  )
}
