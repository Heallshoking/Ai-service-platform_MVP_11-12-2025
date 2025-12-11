"use client"

import { MapPin, Phone, Clock } from "lucide-react"

export default function ContactSection() {
  return (
    <section className="py-16 bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl font-bold text-foreground mb-8 text-center">Контакты</h2>
        
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Contact Info */}
          <div className="space-y-6">
            <div className="flex items-start gap-4 p-6 bg-white rounded-xl shadow-sm border border-border">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Phone className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground mb-1">Телефон</h3>
                <a href="tel:+74012520725" className="text-primary hover:underline text-lg font-semibold">
                  +7 (4012) 52-07-25
                </a>
                <p className="text-sm text-muted-foreground mt-1">Звоните с 10:00 до 19:00</p>
              </div>
            </div>

            <div className="flex items-start gap-4 p-6 bg-white rounded-xl shadow-sm border border-border">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Clock className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground mb-1">Режим работы</h3>
                <p className="text-muted-foreground">Понедельник - Суббота</p>
                <p className="text-primary font-semibold">10:00 - 19:00</p>
                <p className="text-sm text-muted-foreground mt-1">Воскресенье - выходной</p>
              </div>
            </div>

            <div className="flex items-start gap-4 p-6 bg-white rounded-xl shadow-sm border border-border">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <MapPin className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground mb-1">Адрес</h3>
                <p className="text-muted-foreground">Калининград</p>
                <p className="text-sm text-muted-foreground mt-1">Доставка из Москвы</p>
              </div>
            </div>
          </div>

          {/* Map using OpenStreetMap instead of Yandex */}
          <div className="rounded-xl overflow-hidden shadow-lg border border-border h-[400px]">
            <iframe
              src="https://www.openstreetmap.org/export/embed.html?bbox=20.4522%2C54.7065%2C20.5522%2C54.7565&layer=mapnik&marker=54.7315%2C20.5023"
              width="100%"
              height="100%"
              style={{ border: 0 }}
              loading="lazy"
              title="Карта Калининграда"
            ></iframe>
          </div>
        </div>
      </div>
    </section>
  )
}
