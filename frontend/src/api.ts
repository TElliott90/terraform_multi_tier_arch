export type User = { name: string; email: string }

export async function request<T>(path: string, body?: object): Promise<T> {
  const response = await fetch(`/api/${path}`, {
    method: body ? 'POST' : 'GET',
    credentials: 'same-origin',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await response.json()
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.')
  return data
}
