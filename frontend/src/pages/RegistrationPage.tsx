import AuthForm from '../components/AuthForm'
import type { User } from '../api'

export default function RegistrationPage({ onAuthenticated }: { onAuthenticated: (user: User) => void }) {
  return <AuthForm mode="register" onAuthenticated={onAuthenticated} />
}
