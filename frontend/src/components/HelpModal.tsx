import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAppStore } from "../store/useAppStore";
import { getGuide, getConfig } from "../api/client";
import type { GuideSection } from "../api/client";

export default function HelpModal() {
  const open = useAppStore((s) => s.helpOpen);
  const setOpen = useAppStore((s) => s.setHelpOpen);
  const botEmail = useAppStore((s) => s.botEmail);

  const [sections, setSections] = useState<GuideSection[]>([]);
  const [activeTab, setActiveTab] = useState("");
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const backdropRef = useRef<HTMLDivElement>(null);

  // Load guide when modal opens
  useEffect(() => {
    if (!open) return;
    setLoading(true);
    getGuide()
      .then((res) => {
        setSections(res.sections);
        if (res.sections.length > 0 && !activeTab) {
          setActiveTab(res.sections[0].id);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [open]);

  // Resolve bot email: prefer Zustand, fallback to /api/config
  useEffect(() => {
    if (!open) return;
    if (botEmail) {
      setEmail(botEmail);
      return;
    }
    getConfig()
      .then((cfg) => setEmail(cfg.bot_email ?? ""))
      .catch(() => {});
  }, [open, botEmail]);

  // ESC key to close
  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, setOpen]);

  if (!open) return null;

  const activeSection = sections.find((s) => s.id === activeTab);

  async function handleCopy() {
    if (!email) return;
    await navigator.clipboard.writeText(email);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm animate-fade-in"
      onMouseDown={(e) => {
        if (e.target === backdropRef.current) setOpen(false);
      }}
    >
      <div className="w-full max-w-4xl mx-4 bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col h-[80vh] animate-fade-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between px-8 pt-7 pb-2">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-primary text-2xl">
              menu_book
            </span>
            <h2 className="text-xl font-bold text-text-main">User Guide</h2>
          </div>
          <button
            onClick={() => setOpen(false)}
            className="p-2 text-text-muted hover:text-text-main hover:bg-slate-100 rounded-lg transition-colors"
          >
            <span className="material-symbols-outlined text-xl">close</span>
          </button>
        </div>

        {/* Bot email card */}
        {email && (
          <div className="mx-8 mt-3 flex items-center gap-3 bg-primary-light/50 border border-primary/20 rounded-xl p-3">
            <span className="material-symbols-outlined text-primary text-lg">
              mail
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-text-muted">
                Bot Email (시트에 편집자로 초대)
              </p>
              <p className="text-sm font-mono text-text-main truncate">
                {email}
              </p>
            </div>
            <button
              onClick={handleCopy}
              className="shrink-0 p-1.5 rounded-md text-text-muted hover:text-primary hover:bg-primary/5 transition-colors duration-200"
              title="Copy"
            >
              <span className="material-symbols-outlined text-base">
                {copied ? "check" : "content_copy"}
              </span>
            </button>
          </div>
        )}

        {/* Tab bar */}
        {sections.length > 0 && (
          <div className="px-8 pt-4 pb-2 shrink-0">
            <div className="flex gap-0.5 overflow-x-auto bg-slate-100/80 rounded-xl p-1.5 border border-slate-200 scrollbar-hide">
              {sections.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setActiveTab(s.id)}
                  className={`shrink-0 px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 whitespace-nowrap ${
                    activeTab === s.id
                      ? "bg-white text-primary shadow-sm"
                      : "text-slate-500 hover:text-text-main"
                  }`}
                >
                  {s.title}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-8 py-5 custom-scrollbar">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <span className="material-symbols-outlined text-3xl text-primary animate-spin360">
                progress_activity
              </span>
            </div>
          ) : activeSection ? (
            <div className="guide-content">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={mdComponents}
              >
                {activeSection.content}
              </ReactMarkdown>
            </div>
          ) : (
            <div className="text-center py-20 text-text-muted text-sm">
              <span className="material-symbols-outlined text-3xl text-slate-300 mb-2 block">
                menu_book
              </span>
              No guide content available.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Markdown component overrides (Stitch design system) ── */

const mdComponents = {
  h3: ({ children, ...props }: React.ComponentProps<"h3">) => (
    <h3
      className="text-base font-semibold text-text-main mt-6 mb-2"
      {...props}
    >
      {children}
    </h3>
  ),
  h4: ({ children, ...props }: React.ComponentProps<"h4">) => (
    <h4
      className="text-sm font-semibold text-text-main mt-4 mb-1.5"
      {...props}
    >
      {children}
    </h4>
  ),
  p: ({ children, ...props }: React.ComponentProps<"p">) => (
    <p className="text-sm text-text-main leading-relaxed mb-3" {...props}>
      {children}
    </p>
  ),
  ul: ({ children, ...props }: React.ComponentProps<"ul">) => (
    <ul
      className="text-sm text-text-main pl-5 mb-3 space-y-1 list-disc"
      {...props}
    >
      {children}
    </ul>
  ),
  ol: ({ children, ...props }: React.ComponentProps<"ol">) => (
    <ol
      className="text-sm text-text-main pl-5 mb-3 space-y-1 list-decimal"
      {...props}
    >
      {children}
    </ol>
  ),
  li: ({ children, ...props }: React.ComponentProps<"li">) => (
    <li className="leading-relaxed" {...props}>
      {children}
    </li>
  ),
  table: ({ children, ...props }: React.ComponentProps<"table">) => (
    <div className="border border-slate-200 rounded-xl overflow-hidden mb-4">
      <table className="w-full text-sm" {...props}>
        {children}
      </table>
    </div>
  ),
  thead: ({ children, ...props }: React.ComponentProps<"thead">) => (
    <thead className="bg-slate-50 border-b border-slate-200" {...props}>
      {children}
    </thead>
  ),
  th: ({ children, ...props }: React.ComponentProps<"th">) => (
    <th
      className="text-left py-2.5 px-4 font-semibold text-text-muted text-xs uppercase tracking-wider"
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ children, ...props }: React.ComponentProps<"td">) => (
    <td className="py-2.5 px-4 text-text-main" {...props}>
      {children}
    </td>
  ),
  tr: ({ children, ...props }: React.ComponentProps<"tr">) => (
    <tr
      className="border-b border-slate-100 last:border-0"
      {...props}
    >
      {children}
    </tr>
  ),
  blockquote: ({ children, ...props }: React.ComponentProps<"blockquote">) => (
    <blockquote
      className="border-l-2 border-primary pl-3 text-sm text-text-muted bg-blue-50/30 p-3 rounded-r-lg mb-3 [&>p]:mb-0"
      {...props}
    >
      {children}
    </blockquote>
  ),
  code: ({
    className,
    children,
    ...props
  }: React.ComponentProps<"code"> & { inline?: boolean }) => {
    const isBlock = className?.includes("language-");
    if (isBlock) {
      return (
        <code
          className="block bg-slate-50 border border-slate-200 p-3 rounded-lg text-xs font-mono overflow-x-auto mb-3"
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <code
        className="bg-slate-100 px-1.5 py-0.5 rounded text-xs font-mono text-text-main"
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children, ...props }: React.ComponentProps<"pre">) => (
    <pre className="mb-3" {...props}>
      {children}
    </pre>
  ),
  strong: ({ children, ...props }: React.ComponentProps<"strong">) => (
    <strong className="font-semibold text-text-main" {...props}>
      {children}
    </strong>
  ),
  hr: () => null,
  a: ({ children, ...props }: React.ComponentProps<"a">) => (
    <a
      className="text-primary hover:text-primary-dark underline"
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
    </a>
  ),
};
