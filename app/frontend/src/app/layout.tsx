import type { Metadata } from 'next'
import { Roboto_Serif, Roboto_Mono } from 'next/font/google'
import './globals.css'

const robotoSerif = Roboto_Serif({ 
  weight: ['300', '400', '500', '600'],
  subsets: ['latin'],
  variable: '--font-roboto-serif'
})

const robotoMono = Roboto_Mono({ 
  weight: ['300', '400', '500'],
  subsets: ['latin'],
  variable: '--font-roboto-mono'
})

export const metadata: Metadata = {
  title: 'VAT policy simulator',
  description: 'Analyse the impact of VAT registration threshold reforms',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${robotoSerif.variable} ${robotoMono.variable}`}>
      <body className="font-sans">{children}</body>
    </html>
  )
}