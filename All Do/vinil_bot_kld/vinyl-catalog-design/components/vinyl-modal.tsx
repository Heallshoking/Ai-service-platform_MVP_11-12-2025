"use client"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import Image from "next/image"
import { useState } from "react"
import { BookingForm } from "./booking-form"

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

export function VinylModal({
  record,
  open,
  onClose,
}: { record: VinylRecord | null; open: boolean; onClose: () => void }) {
  const [showBooking, setShowBooking] = useState(false)

  if (!record) return null

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-white">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-[#35569C]">{record.title}</DialogTitle>
          <DialogDescription className="text-gray-600">
            {record.artist} • {record.year} • {record.genre || "Рок"}
          </DialogDescription>
        </DialogHeader>

        {showBooking ? (
          <BookingForm
            record={record}
            onBack={() => setShowBooking(false)}
            onSuccess={() => {
              setShowBooking(false)
              onClose()
            }}
          />
        ) : (
          <div className="space-y-6">
            {/* Image Container - Separate for better layout */}
            <div className="relative aspect-square max-w-md mx-auto rounded-xl overflow-hidden bg-gray-100 shadow-2xl">
              <Image src={record.image || "/placeholder.svg"} alt={record.title} fill className="object-cover" />
            </div>

            {/* Details Container */}
            <div className="space-y-4">
              <div className="text-center md:text-left">
                <h3 className="text-2xl font-bold text-gray-800 mb-2">{record.artist}</h3>
                <div className="flex gap-2 justify-center md:justify-start flex-wrap">
                  <span className="bg-gradient-to-r from-[#4e73df] to-[#5a67d8] text-white px-4 py-1.5 rounded-full font-medium text-sm">
                    {record.genre || "Рок"}
                  </span>
                  <span className="bg-gray-100 text-gray-700 px-4 py-1.5 rounded-full font-medium text-sm">
                    {record.year}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm bg-gray-50 rounded-xl p-6 shadow-inner">
                <div>
                  <span className="text-gray-500 block mb-1">Лейбл:</span>
                  <p className="font-semibold text-gray-800">{record.label || "Harvest Records"}</p>
                </div>
                <div>
                  <span className="text-gray-500 block mb-1">Страна:</span>
                  <p className="font-semibold text-gray-800">{record.country}</p>
                </div>
                <div>
                  <span className="text-gray-500 block mb-1">Состояние:</span>
                  <p className="font-semibold text-gray-800">{record.condition || "Отличное"}</p>
                </div>
                <div>
                  <span className="text-gray-500 block mb-1">Цена:</span>
                  <p className="text-2xl font-bold bg-gradient-to-r from-[#f6c23e] to-[#f4b619] bg-clip-text text-transparent">
                    {record.price > 0 ? `${record.price.toLocaleString("ru-RU")} ₽` : "Уточняется"}
                  </p>
                </div>
              </div>

              {/* AI Description */}
              <div className="bg-gradient-to-r from-[#f8f9fa] to-white border-l-4 border-[#f6c23e] rounded-xl p-5 space-y-3 shadow-sm">
                <div className="flex items-center gap-3 text-sm">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#f6c23e] to-[#f4b619] flex items-center justify-center text-gray-800 font-bold shadow-md">
                    AI
                  </div>
                  <div>
                    <p className="font-semibold text-gray-800">AI-музыковед</p>
                    <p className="text-xs text-gray-500">Экспертное описание</p>
                  </div>
                </div>
                <p className="text-sm leading-relaxed text-gray-700">
                  {record.description ||
                    "Эта пластинка — настоящий шедевр прогрессивного рока. Насыщенные звуки, философские тексты и невероятная атмосфера делают её обязательной к прослушиванию. Запись отличается превосходным качеством звука и станет жемчужиной любой коллекции."}
                </p>
              </div>

              <Button
                className="w-full bg-gradient-to-r from-[#4e73df] to-[#5a67d8] hover:from-[#5a67d8] hover:to-[#6f42c1] text-white shadow-lg h-12 text-base font-semibold rounded-xl"
                onClick={() => setShowBooking(true)}
                disabled={record.status === "sold"}
              >
                {record.status === "sold"
                  ? "Продано"
                  : record.status === "preorder"
                    ? "Уведомить о поступлении"
                    : "Забронировать"}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
