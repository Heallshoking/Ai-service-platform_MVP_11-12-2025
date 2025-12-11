"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ArrowLeft, CheckCircle } from "lucide-react"
import { sendTelegramBooking } from "@/app/actions/send-telegram-message"

type VinylRecord = {
  id: string
  title: string
  artist: string
  price: number
}

export function BookingForm({
  record,
  onBack,
  onSuccess,
}: {
  record: VinylRecord
  onBack: () => void
  onSuccess: () => void
}) {
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    address: "",
    comment: "",
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    const result = await sendTelegramBooking({
      recordId: record.id,
      recordTitle: record.title,
      recordArtist: record.artist,
      recordPrice: record.price,
      name: formData.name,
      phone: formData.phone,
      address: formData.address,
      comment: formData.comment,
    })

    setIsSubmitting(false)

    if (result.success) {
      setIsSuccess(true)
      setTimeout(() => {
        onSuccess()
      }, 2000)
    } else {
      alert("Ошибка при отправке. Попробуйте позже.")
    }
  }

  if (isSuccess) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <CheckCircle className="h-16 w-16 text-green-600" />
        <h3 className="text-2xl font-medium">Бронь оформлена!</h3>
        <p className="text-muted-foreground text-center">Мы свяжемся с вами в ближайшее время</p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Button type="button" variant="ghost" onClick={onBack} className="mb-4">
        <ArrowLeft className="h-4 w-4 mr-2" />
        Назад
      </Button>

      <div className="bg-secondary/30 p-4 rounded-lg">
        <p className="text-sm text-muted-foreground">Забронировать:</p>
        <p className="font-medium">
          {record.artist} - {record.title}
        </p>
        <p className="text-xl font-semibold text-gold mt-1">{record.price.toLocaleString("ru-RU")} ₽</p>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="name">Имя *</Label>
          <Input
            id="name"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Иван Иванов"
          />
        </div>

        <div>
          <Label htmlFor="phone">Телефон *</Label>
          <Input
            id="phone"
            type="tel"
            required
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            placeholder="+7 (900) 123-45-67"
          />
        </div>

        <div>
          <Label htmlFor="address">Адрес доставки *</Label>
          <Input
            id="address"
            required
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            placeholder="г. Москва, ул. Ленина, д. 1, кв. 1"
          />
        </div>

        <div>
          <Label htmlFor="comment">Комментарий</Label>
          <Textarea
            id="comment"
            value={formData.comment}
            onChange={(e) => setFormData({ ...formData, comment: e.target.value })}
            placeholder="Дополнительные пожелания..."
            rows={3}
          />
        </div>
      </div>

      <Button type="submit" className="w-full bg-primary hover:bg-primary/90" size="lg" disabled={isSubmitting}>
        {isSubmitting ? "Отправка..." : "Оформить бронь"}
      </Button>
    </form>
  )
}
