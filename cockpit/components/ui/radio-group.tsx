import * as React from "react"
import { Circle } from "lucide-react"
import { cn } from "@/lib/utils"

interface RadioGroupContextValue {
  value?: string
  onValueChange?: (val: string) => void
  disabled?: boolean
}

const RadioGroupContext = React.createContext<RadioGroupContextValue | null>(null)

function RadioGroup({
  value,
  defaultValue,
  onValueChange,
  disabled,
  className,
  children,
  ...props
}: React.ComponentProps<"div"> & {
  value?: string
  defaultValue?: string
  onValueChange?: (val: string) => void
  disabled?: boolean
}) {
  const [internalVal, setInternalVal] = React.useState(defaultValue || "")
  const activeValue = value !== undefined ? value : internalVal

  const handleValueChange = (v: string) => {
    setInternalVal(v)
    onValueChange?.(v)
  }

  return (
    <RadioGroupContext.Provider
      value={{ value: activeValue, onValueChange: handleValueChange, disabled }}
    >
      <div role="radiogroup" className={cn("grid gap-2", className)} {...props}>
        {children}
      </div>
    </RadioGroupContext.Provider>
  )
}

function RadioGroupItem({
  value,
  className,
  disabled,
  id,
  ...props
}: React.ComponentProps<"button"> & { value: string }) {
  const ctx = React.useContext(RadioGroupContext)
  const isChecked = ctx?.value === value
  const isDisabled = disabled || ctx?.disabled

  return (
    <button
      type="button"
      role="radio"
      id={id}
      aria-checked={isChecked}
      disabled={isDisabled}
      onClick={() => !isDisabled && ctx?.onValueChange?.(value)}
      className={cn(
        "aspect-square h-4 w-4 rounded-full border border-primary text-primary ring-offset-background focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 inline-flex items-center justify-center",
        className
      )}
      {...props}
    >
      {isChecked && <Circle className="h-2.5 w-2.5 fill-current text-current" />}
    </button>
  )
}

export { RadioGroup, RadioGroupItem }
