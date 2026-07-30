export type BrowserServerEnvelope =
  | { type: 'screenshot'; payload: { image_base64: string } }
  | { type: 'result'; payload: { message: string } }
  | { type: 'error'; payload: { message: string } }

export type TerminalServerEnvelope =
  | { type: 'output'; data: string }
  | { type: 'closed' }
