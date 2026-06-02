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
  
  const allCookies = request.cookies.getAll()
  const hasRefreshCookie = request.cookies.has('refresh_token')

  console.log(`[Middleware] Path: ${pathname}`)
  console.log(`[Middleware] IsProtected: ${isProtected} | IsAuthRoute: ${isAuthRoute}`)
  console.log(`[Middleware] Cookies:`, allCookies)
  console.log(`[Middleware] Has Refresh Cookie: ${hasRefreshCookie}`)

  if (isProtected && !hasRefreshCookie) {
    console.log(`[Middleware] Redirecting to /login (Protected route missing cookie)`)
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  if (isAuthRoute && hasRefreshCookie) {
    console.log(`[Middleware] Redirecting to /dashboard (Auth route with cookie)`)
    const dashboardUrl = new URL('/dashboard', request.url)
    return NextResponse.redirect(dashboardUrl)
  }

  console.log(`[Middleware] Proceeding normally`)
  return NextResponse.next()
}

export const config = {
  // Run on all routes except next.js internals and API
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|$).*)'],
}
