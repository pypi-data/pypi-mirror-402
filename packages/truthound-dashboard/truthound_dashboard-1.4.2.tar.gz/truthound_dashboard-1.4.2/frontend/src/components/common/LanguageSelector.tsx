/**
 * LanguageSelector Component
 *
 * A dropdown menu for selecting the application language.
 * Currently supports 2 built-in languages: English (en) and Korean (ko).
 * Additional languages can be added via AI translation CLI.
 *
 * Features:
 * - 2 built-in language support with native names and flags
 * - Search/filter functionality
 * - Immediate locale switching
 */
import { useState, useMemo } from 'react'
import { Globe, Check, Search } from 'lucide-react'
import { useLocale, useIntlayer } from 'react-intlayer'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import {
  LOCALE_INFO,
  type LocaleInfo,
  type SupportedLocale,
} from '@/providers/intlayer/config'
import { str } from '@/lib/intlayer-utils'

interface LanguageSelectorProps {
  /** Show only the globe icon (no current language text) */
  iconOnly?: boolean
  /** Custom trigger button className */
  className?: string
  /** Alignment of dropdown content */
  align?: 'start' | 'center' | 'end'
}

/**
 * LanguageSelector - A dropdown for changing the app language
 */
export function LanguageSelector({
  iconOnly = false,
  className = '',
  align = 'end',
}: LanguageSelectorProps) {
  const { locale, setLocale } = useLocale()
  const common = useIntlayer('common')
  const [searchQuery, setSearchQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)

  // Get current locale info
  const currentLocale = useMemo(
    () => LOCALE_INFO.find((l) => l.code === locale) || LOCALE_INFO[0],
    [locale]
  )

  // Filter locales based on search query
  const filteredLocales = useMemo(() => {
    if (!searchQuery.trim()) {
      return LOCALE_INFO
    }

    const query = searchQuery.toLowerCase()
    return LOCALE_INFO.filter(
      (l) =>
        l.name.toLowerCase().includes(query) ||
        l.nativeName.toLowerCase().includes(query) ||
        l.code.toLowerCase().includes(query)
    )
  }, [searchQuery])

  const handleSelect = (localeCode: SupportedLocale) => {
    setLocale(localeCode)
    setIsOpen(false)
    setSearchQuery('')
  }

  const renderLocaleItem = (localeInfo: LocaleInfo) => (
    <DropdownMenuItem
      key={localeInfo.code}
      onClick={() => handleSelect(localeInfo.code)}
      className="flex items-center justify-between gap-2 cursor-pointer"
    >
      <span className="flex items-center gap-2">
        <span className="text-base">{localeInfo.flag}</span>
        <span>{localeInfo.nativeName}</span>
        {localeInfo.rtl && (
          <span className="text-xs text-muted-foreground px-1 py-0.5 bg-muted rounded">
            RTL
          </span>
        )}
      </span>
      {locale === localeInfo.code && (
        <Check className="h-4 w-4 text-primary" />
      )}
    </DropdownMenuItem>
  )

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size={iconOnly ? 'icon' : 'default'}
          className={className}
        >
          <Globe className="h-4 w-4" />
          {!iconOnly && (
            <span className="ml-2 flex items-center gap-1">
              <span>{currentLocale.flag}</span>
              <span className="hidden sm:inline">{currentLocale.nativeName}</span>
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={align} className="w-[300px] overflow-x-hidden">
        {/* Search input - fixed, not scrollable */}
        <div className="p-2 border-b">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={str(common.search)}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-9"
            />
          </div>
        </div>

        {/* Scrollable content area */}
        <div className="max-h-[300px] overflow-y-auto overflow-x-hidden">
          {/* Available languages */}
          {filteredLocales.length > 0 && (
            <>
              {filteredLocales.map(renderLocaleItem)}
            </>
          )}

          {/* No results */}
          {filteredLocales.length === 0 && (
            <div className="p-4 text-center text-sm text-muted-foreground">
              {str(common.noResults)}
            </div>
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default LanguageSelector
