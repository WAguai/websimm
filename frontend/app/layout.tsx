import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Game Generator',
  description: 'Generate interactive games with AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
}