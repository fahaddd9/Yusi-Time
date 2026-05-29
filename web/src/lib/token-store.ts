// Module-level variable — NEVER localStorage, NEVER sessionStorage
let accessToken: string | null = null

export const tokenStore = {
  getAccessToken: () => accessToken,
  setAccessToken: (token: string) => { accessToken = token },
  clearAccessToken: () => { accessToken = null },
}
