export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  role: 'admin' | 'member'
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}
