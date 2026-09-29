import { useState } from 'react'
import type { FormEvent } from 'react'
import { request } from '../api'
import type { User } from '../api'

export default function AuthForm({ mode, onAuthenticated }: {
  mode: 'login' | 'register'; onAuthenticated: (user: User) => void
}) {
  const registering = mode === 'register'
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [visible, setVisible] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const fields = new FormData(event.currentTarget)
    setError('')
    if (registering && fields.get('password') !== fields.get('confirm')) {
      setError('Your passwords don’t match. Please try again.')
      return
    }
    setBusy(true)
    try {
      const result = await request<{ user: User }>(mode, {
        name: fields.get('name'), email: fields.get('email'), password: fields.get('password'),
      })
      onAuthenticated(result.user)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to connect. Please try again.')
    } finally { setBusy(false) }
  }

  return <>
    <p className="eyebrow">YOUR PERSONAL SPACE</p>
    <h1>{registering ? 'Make yourself at home.' : 'Welcome back.'}</h1>
    <p className="intro">{registering ? 'Create an account to get started.' : 'Enter your details to sign in to your account.'}</p>
    <form onSubmit={submit}>
      <fieldset disabled={busy}>
        {registering && <label>Full name<input name="name" autoComplete="name" placeholder="Alex Morgan" required maxLength={100} /></label>}
        <label>Email address<input name="email" type="email" autoComplete="email" placeholder="you@example.com" required maxLength={254} /></label>
        <label>Password<span className="password-field"><input name="password" type={visible ? 'text' : 'password'} autoComplete={registering ? 'new-password' : 'current-password'} placeholder="Enter your password" required minLength={registering ? 8 : undefined} maxLength={128} aria-describedby={registering ? 'password-help' : undefined} /><button type="button" className="reveal" onClick={() => setVisible(!visible)} aria-pressed={visible} aria-label={visible ? 'Hide password' : 'Show password'}>{visible ? 'Hide' : 'Show'}</button></span></label>
        {registering && <><p className="hint" id="password-help">Use at least 8 characters.</p><label>Confirm password<input name="confirm" type={visible ? 'text' : 'password'} autoComplete="new-password" placeholder="Re-enter your password" required maxLength={128} /></label></>}
        {error && <p className="error" role="alert">{error}</p>}
        <button className="primary" type="submit">{busy ? 'Please wait…' : registering ? 'Create account' : 'Sign in'} <span aria-hidden="true">→</span></button>
      </fieldset>
    </form>
    <p className="switch">{registering ? 'Already have an account?' : 'New here?'} <a href={registering ? '#login' : '#register'}>{registering ? 'Sign in' : 'Create an account'}</a></p>
  </>
}
