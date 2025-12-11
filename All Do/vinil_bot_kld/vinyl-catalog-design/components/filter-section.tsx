"use client"

import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"

type FilterSectionProps = {
  title: string
  options: string[]
  selected: string[]
  onChange: (selected: string[]) => void
}

export function FilterSection({ title, options, selected, onChange }: FilterSectionProps) {
  const handleToggle = (option: string) => {
    if (selected.includes(option)) {
      onChange(selected.filter((item) => item !== option))
    } else {
      onChange([...selected, option])
    }
  }

  return (
    <div className="space-y-3">
      <label className="text-sm text-muted-foreground">{title}</label>
      <div className="space-y-2">
        {options.map((option) => (
          <div key={option} className="flex items-center space-x-2">
            <Checkbox
              id={`${title}-${option}`}
              checked={selected.includes(option)}
              onCheckedChange={() => handleToggle(option)}
              className="border-gold/30 data-[state=checked]:bg-gold data-[state=checked]:border-gold"
            />
            <Label
              htmlFor={`${title}-${option}`}
              className="text-sm font-normal cursor-pointer hover:text-gold transition-colors"
            >
              {option}
            </Label>
          </div>
        ))}
      </div>
    </div>
  )
}
