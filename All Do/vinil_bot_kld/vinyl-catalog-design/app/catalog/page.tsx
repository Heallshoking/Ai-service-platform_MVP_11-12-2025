import CatalogClient from "./catalogClient"

const API_URL = "http://176.98.178.109:8000"

export const metadata = {
  title: "Все категории | BALT-SET",
  description: "Полный каталог виниловых пластинок в Калининграде - balt-set.ru",
}

async function getRecords() {
  let records = []
  try {
    const res = await fetch(`${API_URL}/api/records`, {
      next: { revalidate: 60 },
    })
    const data = await res.json()
    records = data.records || []
  } catch (error) {
    console.error("Ошибка загрузки каталога:", error)
  }
  return records
}

export default async function CatalogPage() {
  const records = await getRecords()
  const categories = ["Рок", "Джаз", "Классика", "Электроника", "Поп", "СССР"]

  return <CatalogClient records={records} categories={categories} />
}
