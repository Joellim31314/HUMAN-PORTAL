"use client"

import { useSyncExternalStore } from "react"

import type { ProductAnswers } from "@/lib/types"

const PROFILE_KEY = "hp-product-profile"
const COUNT_KEY = "hp-searches-left"
const INITIAL_COUNT = 35

// Cached snapshots — useSyncExternalStore requires getSnapshot to return a
// stable reference between store notifications.
let productCache: ProductAnswers | null | undefined
let countCache: number | undefined

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback)
  window.addEventListener("hp-storage", callback)
  return () => {
    window.removeEventListener("storage", callback)
    window.removeEventListener("hp-storage", callback)
  }
}

function notify() {
  window.dispatchEvent(new Event("hp-storage"))
}

export function saveProduct(product: ProductAnswers) {
  localStorage.setItem(PROFILE_KEY, JSON.stringify(product))
  productCache = product
  notify()
}

export function loadProduct(): ProductAnswers | null {
  if (productCache !== undefined) return productCache
  try {
    const raw = localStorage.getItem(PROFILE_KEY)
    productCache = raw ? (JSON.parse(raw) as ProductAnswers) : null
  } catch {
    productCache = null
  }
  return productCache
}

export function clearProduct() {
  localStorage.removeItem(PROFILE_KEY)
  productCache = null
  notify()
}

export function getSearchesLeft(): number {
  if (countCache !== undefined) return countCache
  const raw = localStorage.getItem(COUNT_KEY)
  countCache = raw === null ? INITIAL_COUNT : Number(raw)
  return countCache
}

export function decrementSearches() {
  countCache = Math.max(0, getSearchesLeft() - 1)
  localStorage.setItem(COUNT_KEY, String(countCache))
  notify()
}

export function resetDemoData() {
  localStorage.removeItem(COUNT_KEY)
  localStorage.removeItem(PROFILE_KEY)
  countCache = INITIAL_COUNT
  productCache = null
  notify()
}

export function useProduct(): ProductAnswers | null {
  return useSyncExternalStore(
    subscribe,
    () => loadProduct(),
    () => null
  )
}

export function useSearchesLeft(): number {
  return useSyncExternalStore(
    subscribe,
    () => getSearchesLeft(),
    () => INITIAL_COUNT
  )
}
