import type { Metadata } from 'next'
import { DM_Sans, DM_Mono } from 'next/font/google'
import { ThemeProvider } from '@/components/ThemeProvider'
import { QueryClientWrapper } from '@/components/QueryClientWrapper'
import { Toaster } from 'sonner'
import { MotionConfigWrapper } from '@/components/MotionConfigWrapper'
import './globals.css'
import { TooltipProvider } from '@/components/ui/tooltip'

const dmSans = DM_Sans({ subsets: ['latin'], variable: '--font-sans' })
const dmMono = DM_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
})

export const metadata: Metadata = {
  title: 'Yusi Time — Smart Time Tracking',
  description: 'Track time, manage approvals, and get paid faster.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${dmSans.variable} ${dmMono.variable} font-sans antialiased bg-background text-foreground`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryClientWrapper>
            <MotionConfigWrapper>
              <TooltipProvider>
                {children}
              </TooltipProvider>
              <Toaster position="bottom-right" richColors />
            </MotionConfigWrapper>
          </QueryClientWrapper>
        </ThemeProvider>
      </body>
    </html>
  )
}
