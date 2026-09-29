import AuthForm from '../components/AuthForm'
import type { User } from '../api'

export default function LoginPage({ onAuthenticated }: { onAuthenticated: (user: User) => void }) {
  return <AuthForm mode="login" onAuthenticated={onAuthenticated} />
}
