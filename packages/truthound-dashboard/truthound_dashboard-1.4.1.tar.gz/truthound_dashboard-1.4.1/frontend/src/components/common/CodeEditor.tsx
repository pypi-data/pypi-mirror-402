/**
 * CodeEditor - A lightweight, reusable code editor component.
 *
 * Features:
 * - Line numbers
 * - Basic syntax highlighting via CSS classes
 * - Auto-indent support
 * - Error highlighting
 * - Customizable styling
 * - Keyboard shortcuts (Tab for indent)
 *
 * This component uses a simple textarea-based approach with CSS styling
 * to avoid heavy dependencies like Monaco Editor.
 */

import {
  useState,
  useRef,
  useCallback,
  forwardRef,
  useImperativeHandle,
  type ChangeEvent,
  type KeyboardEvent,
  type TextareaHTMLAttributes,
} from 'react'
import { cn } from '@/lib/utils'

export interface CodeEditorProps
  extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'onChange' | 'value'> {
  /** The code value */
  value: string
  /** Change handler */
  onChange: (value: string) => void
  /** Programming language for syntax highlighting */
  language?: 'python' | 'jinja2' | 'json' | 'plain'
  /** Show line numbers */
  showLineNumbers?: boolean
  /** Tab size for indentation */
  tabSize?: number
  /** Minimum number of visible lines */
  minLines?: number
  /** Maximum number of visible lines */
  maxLines?: number
  /** Error line numbers to highlight */
  errorLines?: number[]
  /** Whether the editor is read-only */
  readOnly?: boolean
  /** Placeholder text */
  placeholder?: string
  /** Additional class name for the container */
  containerClassName?: string
  /** Whether to wrap long lines */
  wordWrap?: boolean
  /** On blur handler */
  onBlur?: () => void
  /** On focus handler */
  onFocus?: () => void
}

export interface CodeEditorRef {
  /** Focus the editor */
  focus: () => void
  /** Blur the editor */
  blur: () => void
  /** Insert text at cursor position */
  insertAtCursor: (text: string) => void
  /** Get current cursor position */
  getCursorPosition: () => number
  /** Set cursor position */
  setCursorPosition: (position: number) => void
  /** Select a range */
  setSelection: (start: number, end: number) => void
}

/**
 * Calculate line height based on font metrics.
 */
const LINE_HEIGHT = 20 // px

/**
 * CodeEditor component with line numbers and basic syntax highlighting.
 */
export const CodeEditor = forwardRef<CodeEditorRef, CodeEditorProps>(
  (
    {
      value,
      onChange,
      language = 'python',
      showLineNumbers = true,
      tabSize = 2,
      minLines = 5,
      maxLines = 20,
      errorLines = [],
      readOnly = false,
      placeholder,
      containerClassName,
      wordWrap = false,
      onBlur,
      onFocus,
      className,
      ...textareaProps
    },
    ref
  ) => {
    const textareaRef = useRef<HTMLTextAreaElement>(null)
    const lineNumbersRef = useRef<HTMLDivElement>(null)
    const [isFocused, setIsFocused] = useState(false)

    // Calculate line count
    const lines = value.split('\n')
    const lineCount = lines.length

    // Calculate height based on line count
    const minHeight = minLines * LINE_HEIGHT
    const maxHeight = maxLines * LINE_HEIGHT
    const contentHeight = lineCount * LINE_HEIGHT
    const height = Math.min(Math.max(contentHeight, minHeight), maxHeight)

    // Sync scroll between textarea and line numbers
    const handleScroll = useCallback(() => {
      if (textareaRef.current && lineNumbersRef.current) {
        lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop
      }
    }, [])

    // Handle text change
    const handleChange = useCallback(
      (e: ChangeEvent<HTMLTextAreaElement>) => {
        onChange(e.target.value)
      },
      [onChange]
    )

    // Handle keyboard events for auto-indent
    const handleKeyDown = useCallback(
      (e: KeyboardEvent<HTMLTextAreaElement>) => {
        const textarea = textareaRef.current
        if (!textarea || readOnly) return

        // Tab key - insert spaces
        if (e.key === 'Tab') {
          e.preventDefault()
          const start = textarea.selectionStart
          const end = textarea.selectionEnd
          const spaces = ' '.repeat(tabSize)

          if (e.shiftKey) {
            // Shift+Tab: Remove indent from current line(s)
            const lineStart = value.lastIndexOf('\n', start - 1) + 1
            const lineEnd = value.indexOf('\n', end)
            const actualEnd = lineEnd === -1 ? value.length : lineEnd

            const beforeLines = value.substring(0, lineStart)
            const selectedLines = value.substring(lineStart, actualEnd)
            const afterLines = value.substring(actualEnd)

            // Remove leading spaces from each line
            const dedentedLines = selectedLines
              .split('\n')
              .map((line) => {
                if (line.startsWith(spaces)) {
                  return line.substring(tabSize)
                } else if (line.startsWith(' ')) {
                  return line.replace(/^ +/, '')
                }
                return line
              })
              .join('\n')

            const newValue = beforeLines + dedentedLines + afterLines
            onChange(newValue)

            // Restore cursor
            const diff = selectedLines.length - dedentedLines.length
            requestAnimationFrame(() => {
              textarea.setSelectionRange(
                Math.max(lineStart, start - tabSize),
                Math.max(lineStart, end - diff)
              )
            })
          } else {
            // Tab: Insert spaces
            const newValue = value.substring(0, start) + spaces + value.substring(end)
            onChange(newValue)

            // Move cursor after inserted spaces
            requestAnimationFrame(() => {
              textarea.setSelectionRange(start + tabSize, start + tabSize)
            })
          }
        }

        // Enter key - maintain indent
        if (e.key === 'Enter') {
          e.preventDefault()
          const start = textarea.selectionStart
          const lineStart = value.lastIndexOf('\n', start - 1) + 1
          const currentLine = value.substring(lineStart, start)
          const indent = currentLine.match(/^[ ]*/)?.[0] || ''

          // Add extra indent after colon (Python)
          const extraIndent =
            language === 'python' && currentLine.trimEnd().endsWith(':')
              ? ' '.repeat(tabSize)
              : ''

          const newValue =
            value.substring(0, start) + '\n' + indent + extraIndent + value.substring(start)
          onChange(newValue)

          // Move cursor to after indent
          const newCursorPos = start + 1 + indent.length + extraIndent.length
          requestAnimationFrame(() => {
            textarea.setSelectionRange(newCursorPos, newCursorPos)
          })
        }
      },
      [value, onChange, tabSize, language, readOnly]
    )

    // Handle focus
    const handleFocus = useCallback(() => {
      setIsFocused(true)
      onFocus?.()
    }, [onFocus])

    // Handle blur
    const handleBlur = useCallback(() => {
      setIsFocused(false)
      onBlur?.()
    }, [onBlur])

    // Expose imperative methods
    useImperativeHandle(
      ref,
      () => ({
        focus: () => textareaRef.current?.focus(),
        blur: () => textareaRef.current?.blur(),
        insertAtCursor: (text: string) => {
          const textarea = textareaRef.current
          if (!textarea) return

          const start = textarea.selectionStart
          const end = textarea.selectionEnd
          const newValue = value.substring(0, start) + text + value.substring(end)
          onChange(newValue)

          requestAnimationFrame(() => {
            textarea.setSelectionRange(start + text.length, start + text.length)
            textarea.focus()
          })
        },
        getCursorPosition: () => textareaRef.current?.selectionStart ?? 0,
        setCursorPosition: (position: number) => {
          const textarea = textareaRef.current
          if (!textarea) return
          textarea.setSelectionRange(position, position)
        },
        setSelection: (start: number, end: number) => {
          const textarea = textareaRef.current
          if (!textarea) return
          textarea.setSelectionRange(start, end)
        },
      }),
      [value, onChange]
    )

    // Render line numbers
    const renderLineNumbers = () => {
      if (!showLineNumbers) return null

      return (
        <div
          ref={lineNumbersRef}
          className={cn(
            'flex-shrink-0 select-none overflow-hidden',
            'bg-muted/30 text-muted-foreground text-right',
            'font-mono text-sm py-2 pr-2 pl-3',
            'border-r border-border'
          )}
          style={{ lineHeight: `${LINE_HEIGHT}px`, height }}
          aria-hidden="true"
        >
          {lines.map((_, index) => {
            const lineNum = index + 1
            const isError = errorLines.includes(lineNum)
            return (
              <div
                key={index}
                className={cn(
                  'pr-2',
                  isError && 'text-destructive font-medium bg-destructive/10'
                )}
              >
                {lineNum}
              </div>
            )
          })}
        </div>
      )
    }

    return (
      <div
        className={cn(
          'relative flex rounded-md border bg-background',
          'transition-colors',
          isFocused && 'ring-2 ring-ring ring-offset-2 ring-offset-background',
          readOnly && 'bg-muted/20',
          containerClassName
        )}
      >
        {renderLineNumbers()}
        <div className="relative flex-1 overflow-hidden">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onScroll={handleScroll}
            onFocus={handleFocus}
            onBlur={handleBlur}
            readOnly={readOnly}
            placeholder={placeholder}
            spellCheck={false}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            className={cn(
              'w-full resize-none',
              'font-mono text-sm leading-5',
              'py-2 px-3',
              'bg-transparent',
              'focus:outline-none',
              'placeholder:text-muted-foreground/50',
              wordWrap ? 'whitespace-pre-wrap break-words' : 'whitespace-pre overflow-x-auto',
              className
            )}
            style={{
              lineHeight: `${LINE_HEIGHT}px`,
              height,
              tabSize,
              MozTabSize: tabSize,
            }}
            {...textareaProps}
          />
        </div>
      </div>
    )
  }
)

CodeEditor.displayName = 'CodeEditor'

export default CodeEditor
