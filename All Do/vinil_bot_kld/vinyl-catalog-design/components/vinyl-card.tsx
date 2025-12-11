"use client"

import { Card } from "@/components/ui/card"
import Image from "next/image"
import { useRouter } from "next/navigation"

type VinylRecord = {
  id: string
  title: string
  artist: string
  year: number
  country: string
  price: number
  status: "available" | "reserved" | "sold" | "preorder"
  image: string
  genre?: string
  label?: string
  condition?: string
  description?: string
}

export function VinylCard({
  record,
  compact = false,
}: {
  record: VinylRecord
  compact?: boolean
}) {
  const router = useRouter()
  const statusConfig = {
    available: {
      label: "Доступна",
      className: "bg-emerald-500 text-white",
    },
    reserved: {
      label: "Резерв",
      className: "bg-amber-500 text-white",
    },
    sold: {
      label: "Продана",
      className: "bg-gray-500 text-white",
    },
    preorder: {
      label: "Предзаказ",
      className: "bg-blue-500 text-white",
    },
  }

  const status = statusConfig[record.status]
  const handleClick = () => {
    router.push(`/vinyl/${record.id}`)
  }

  if (compact) {
    return (
      <div
        className="group relative cursor-pointer transition-all duration-300 hover:-translate-y-1"
        onClick={handleClick}
      >
        <div className="relative aspect-square overflow-hidden rounded-lg bg-secondary shadow-md group-hover:shadow-xl transition-shadow duration-300">
          <Image
            src={record.image || "/placeholder.svg"}
            alt={`${record.artist} - ${record.title}`}
            fill
            className="object-cover"
          />

          <div className={`absolute top-2 right-2 px-2.5 py-1 rounded-full text-xs font-medium ${status.className}`}>
            {status.label}
          </div>

          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
            <p className="text-white text-sm font-semibold line-clamp-2 mb-1">{record.title}</p>
            <p className="text-white/90 text-xs line-clamp-1 mb-2">{record.artist}</p>
            <div className="flex items-center justify-between">
              <span className="text-white/70 text-xs">{record.year}</span>
              <span className="text-accent text-sm font-bold">{record.price.toLocaleString("ru-RU")} ₽</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Card
      className="group relative overflow-hidden bg-card border border-border hover:border-primary/50 hover:shadow-lg transition-all duration-300 cursor-pointer"
      onClick={handleClick}
    >
      <div className="relative aspect-square overflow-hidden bg-secondary">
        <Image
          src={record.image || "/placeholder.svg"}
          alt={`${record.artist} - ${record.title}`}
          fill
          className="object-cover transition-transform duration-500 group-hover:scale-105"
        />

        <div className={`absolute top-3 right-3 px-3 py-1 rounded-full text-xs font-medium ${status.className}`}>
          {status.label}
        </div>
      </div>

      <div className="p-4 space-y-2 bg-card">
        <h3 className="font-semibold text-base text-pretty leading-tight text-foreground group-hover:text-primary transition-colors line-clamp-2">
          {record.title}
        </h3>
        <p className="text-sm text-muted-foreground line-clamp-1">{record.artist}</p>

        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-muted-foreground">
            {record.year} • {record.country}
          </span>
          <div className="text-lg font-bold text-accent">{record.price.toLocaleString("ru-RU")} ₽</div>
        </div>
      </div>
    </Card>
  )
}
