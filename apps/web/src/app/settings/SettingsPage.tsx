import { PageHeader } from '@/components/layout/PageHeader'
import { Card } from '@/components/ui/card'
import { useAuthStore } from '@/store/auth-store'

export function SettingsPage() {
  const user = useAuthStore((s) => s.user)

  return (
    <>
      <PageHeader title="Einstellungen" subtitle="Konto & System" />
      <Card className="max-w-lg">
        <div className="font-mono text-[11px] uppercase tracking-wider text-text-low">Konto</div>
        <dl className="mt-3 space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-text-mid">Name</dt>
            <dd className="text-text-hi">{user?.full_name}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-text-mid">E-Mail</dt>
            <dd className="text-text-hi">{user?.email}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-text-mid">Rolle</dt>
            <dd className="text-text-hi">{user?.role}</dd>
          </div>
        </dl>
      </Card>
      <Card className="mt-4 max-w-lg">
        <div className="font-mono text-[11px] uppercase tracking-wider text-text-low">API-Keys</div>
        <p className="mt-2 text-sm text-text-mid">
          Verschluesselte Verwaltung von Provider-API-Keys (OpenAI, Anthropic, ElevenLabs, ...) kommt mit
          Phase 1 (Model-Abstraction).
        </p>
      </Card>
    </>
  )
}
