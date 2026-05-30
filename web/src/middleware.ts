import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// These are all the protected routes that require authentication
const protectedPrefixes = [
  '/dashboard',
  '/timesheet',
  '/projects',
  '/reports',
  '/approvals',
  '/settings',
]

// Auth routes where logged-in users shouldn't be
const authRoutes = [
  '/login',
  '/signup',
  '/forgot-password',
  '/reset-password',
]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  const isProtected = protectedPrefixes.some((p) => pathname.startsWith(p))
  const isAuthRoute = authRoutes.some((p) => pathname.startsWith(p))
  
  const hasRefreshCookie = request.cookies.has('refresh_token')

  if (isProtected && !hasRefreshCookie) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  if (isAuthRoute && hasRefreshCookie) {
    const dashboardUrl = new URL('/dashboard', request.url)
    return NextResponse.redirect(dashboardUrl)
  }

  return NextResponse.next()
}

export const config = {
  // Run on all routes except next.js internals and API
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|$).*)'],
}
