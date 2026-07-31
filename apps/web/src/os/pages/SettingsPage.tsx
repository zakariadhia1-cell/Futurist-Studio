import { useState } from 'react'
import { Database, KeyRound, Moon, Settings, Shield, Sun, Users } from 'lucide-react'
import { GlassCard } from '../components/GlassCard'
import { SectionHeader } from '../components/SectionHeader'
import { LoadingState } from '../components/LoadingState'
import { Badge } from '../components/Badge'
import { getApiKeys, getBackups, getSettingsUsers } from '../data/mock'
import { useMock } from '../data/useMock'

export function SettingsPage() {
  const { data: users, loading: usersLoading } = useMock(getSettingsUsers)
  const { data: apiKeys, loading: keysLoading } = useMock(getApiKeys)
  const { data: backups, loading: backupsLoading } = useMock(getBackups)
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [twoFactor, setTwoFactor] = useState(false)

  return (
    <>
      <SectionHeader icon={Settings} title="Einstellungen" subtitle="Benutzer, Rollen, API-Keys, Sicherheit, Backup und Darstellung" />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GlassCard>
          <div className="mb-3 flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-white/45">
            <Users className="h-3.5 w-3.5" /> Benutzer & Rollen
          </div>
          {usersLoading || !users ? (
            <LoadingState />
          ) : (
            <div className="space-y-2.5">
              {users.map((u) => (
                <div key={u.id} className="flex items-center justify-between rounded-lg border border-white/10 px-3.5 py-2.5">
                  <div>
                    <div className="text-sm text-white/85">{u.name}</div>
                    <div className="text-xs text-white/35">{u.email}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge tone={u.role === 'admin' ? 'info' : 'neutral'}>{u.role}</Badge>
                    <Badge tone={u.active ? 'ok' : 'danger'} dot>
                      {u.active ? 'aktiv' : 'inaktiv'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        <GlassCard>
          <div className="mb-3 flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-white/45">
            <KeyRound className="h-3.5 w-3.5" /> API-Keys
          </div>
          {keysLoading || !apiKeys ? (
            <LoadingState />
          ) : (
            <div className="space-y-2.5">
              {apiKeys.map((key) => (
                <div key={key.id} className="flex items-center justify-between rounded-lg border border-white/10 px-3.5 py-2.5">
                  <div>
                    <div className="text-sm text-white/85">{key.label}</div>
                    <div className="font-mono text-xs text-white/35">{key.maskedKey}</div>
                  </div>
                  <Badge tone={key.status === 'aktiv' ? 'ok' : 'warn'}>{key.status}</Badge>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        <GlassCard>
          <div className="mb-3 flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-white/45">
            <Shield className="h-3.5 w-3.5" /> Sicherheit
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-white/85">Zwei-Faktor-Authentifizierung</div>
                <div className="text-xs text-white/35">Zusaetzlicher Schutz beim Login</div>
              </div>
              <button
                onClick={() => setTwoFactor((v) => !v)}
                className={`relative h-6 w-11 rounded-full transition-colors ${twoFactor ? 'bg-[color:var(--color-neon-blue)]' : 'bg-white/10'}`}
              >
                <span
                  className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${twoFactor ? 'translate-x-5' : 'translate-x-0.5'}`}
                />
              </button>
            </div>
            <div className="flex items-center justify-between border-t border-white/10 pt-3">
              <div className="text-sm text-white/85">Aktive Sitzungen</div>
              <span className="text-xs text-white/40">2 Geraete</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-sm text-white/85">Letztes Passwort-Update</div>
              <span className="text-xs text-white/40">vor 34 Tagen</span>
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="mb-3 flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-white/45">
            <Database className="h-3.5 w-3.5" /> Backup
          </div>
          {backupsLoading || !backups ? (
            <LoadingState />
          ) : (
            <div className="space-y-2.5">
              {backups.map((b) => (
                <div key={b.id} className="flex items-center justify-between rounded-lg border border-white/10 px-3.5 py-2.5">
                  <div>
                    <div className="text-sm text-white/85">{b.createdAt}</div>
                    <div className="text-xs text-white/35">{b.sizeMb > 0 ? `${b.sizeMb} MB` : '-'}</div>
                  </div>
                  <Badge tone={b.status === 'erfolgreich' ? 'ok' : 'danger'}>{b.status}</Badge>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>

      <GlassCard className="mt-4">
        <div className="mb-3 font-mono text-[11px] uppercase tracking-wider text-white/45">Theme</div>
        <div className="flex gap-3">
          <button
            onClick={() => setTheme('dark')}
            className={`flex flex-1 items-center justify-center gap-2 rounded-lg border py-2.5 text-sm transition-colors ${
              theme === 'dark' ? 'border-[color:var(--color-neon-blue)]/40 bg-[color:var(--color-neon-blue)]/10 text-white' : 'border-white/10 text-white/50'
            }`}
          >
            <Moon className="h-4 w-4" strokeWidth={1.75} /> Dunkel (Neon)
          </button>
          <button
            onClick={() => setTheme('light')}
            className={`flex flex-1 items-center justify-center gap-2 rounded-lg border py-2.5 text-sm transition-colors ${
              theme === 'light' ? 'border-[color:var(--color-neon-blue)]/40 bg-[color:var(--color-neon-blue)]/10 text-white' : 'border-white/10 text-white/50'
            }`}
          >
            <Sun className="h-4 w-4" strokeWidth={1.75} /> Hell
          </button>
        </div>
        <p className="mt-2 text-xs text-white/30">
          Das Kontrollzentrum ist aktuell fest im Neon-Dark-Theme gestaltet - die Umschaltung ist als UI vorbereitet, ein
          helles Theme folgt spaeter.
        </p>
      </GlassCard>
    </>
  )
}
