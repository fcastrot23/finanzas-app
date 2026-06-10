import type { Currency } from "@/types/finance";

const currencyFormatters: Record<Currency, Intl.NumberFormat> = {
  CRC: new Intl.NumberFormat("es-CR", {
    style: "currency",
    currency: "CRC",
    maximumFractionDigits: 0,
  }),
  USD: new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }),
};

export function formatMoney(amount: number, currency: Currency) {
  return currencyFormatters[currency].format(amount);
}

export function formatCompactMoney(amount: number, currency: Currency) {
  if (currency === "CRC") {
    return `₡${new Intl.NumberFormat("es-CR", {
      maximumFractionDigits: 0,
    }).format(amount)}`;
  }

  return `$${new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(amount)}`;
}
