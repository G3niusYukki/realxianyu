import 'axios'

declare module 'axios' {
  interface AxiosError {
    userMessage?: string
    userAction?: string
    isUserFriendly?: boolean
    statusCode?: number
  }
}
