import { useState, useEffect, useRef } from "react";
import { useAppStore } from "../store/useAppStore";
import { getConfig, saveConfig } from "../api/client";
import { useFocusTrap } from "../hooks/useFocusTrap";

type Tab = "prompting" | "glossary";
type GlossaryLang = "ja" | "en";

const LANG_LABELS: Record<GlossaryLang, string> = {
  ja: "Japanese (JA)",
  en: "English (EN)",
};

export default function SettingsModal() {
  const open = useAppStore((s) => s.settingsOpen);
  const setOpen = useAppStore((s) => s.setSettingsOpen);
  const selectedSheet = useAppStore((s) => s.selectedSheet);
  const customPrompts = useAppStore((s) => s.customPrompts);
  const setGlossary = useAppStore((s) => s.setGlossary);
  const setCustomPrompts = useAppStore((s) => s.setCustomPrompts);

  const [tab, setTab] = useState<Tab>("prompting");
  const [synopsisText, setSynopsisText] = useState("");
  const [toneText, setToneText] = useState("");
  const [promptText, setPromptText] = useState("");
  const [localGlossary, setLocalGlossary] = useState<
    Record<string, Record<string, string>>
  >({});
  const [glossaryLang, setGlossaryLang] = useState<GlossaryLang>("ja");
  const [newSource, setNewSource] = useState("");
  const [newTarget, setNewTarget] = useState("");
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const backdropRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useFocusTrap(panelRef, open);

  // Load config when modal opens
  useEffect(() => {
    if (!open) {
      setLoaded(false);
      return;
    }
    getConfig()
      .then((cfg) => {
        const g = cfg.glossary ?? {};
        const p = cfg.custom_prompts ?? {};
        setLocalGlossary(g);
        setGlossary(g);
        setCustomPrompts(p);
        setSynopsisText(cfg.game_synopsis ?? "");
        setToneText(cfg.tone_and_manner ?? "");
        setPromptText(selectedSheet ? p[selectedSheet] ?? "" : "");
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, [open]);

  // Update prompt text when sheet changes while modal is open
  useEffect(() => {
    if (open && loaded) {
      setPromptText(selectedSheet ? customPrompts[selectedSheet] ?? "" : "");
    }
  }, [selectedSheet, open, loaded]);

  if (!open) return null;

  const currentEntries = Object.entries(localGlossary[glossaryLang] ?? {});

  function handleAddEntry() {
    const src = newSource.trim();
    const tgt = newTarget.trim();
    if (!src || !tgt) return;
    setLocalGlossary((prev) => ({
      ...prev,
      [glossaryLang]: { ...prev[glossaryLang], [src]: tgt },
    }));
    setNewSource("");
    setNewTarget("");
  }

  function handleDeleteEntry(key: string) {
    setLocalGlossary((prev) => {
      const langEntries = { ...prev[glossaryLang] };
      delete langEntries[key];
      return { ...prev, [glossaryLang]: langEntries };
    });
  }

  async function handleSave() {
    setSaving(true);
    const updatedPrompts = { ...customPrompts };
    if (selectedSheet) {
      if (promptText.trim()) {
        updatedPrompts[selectedSheet] = promptText.trim();
      } else {
        delete updatedPrompts[selectedSheet];
      }
    }
    try {
      await saveConfig({
        glossary: localGlossary,
        custom_prompts: updatedPrompts,
        game_synopsis: synopsisText.trim() || undefined,
        tone_and_manner: toneText.trim() || undefined,
      });
      setGlossary(localGlossary);
      setCustomPrompts(updatedPrompts);
      setOpen(false);
    } catch {
      // silent — config save is non-critical
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm animate-fade-in"
      onMouseDown={(e) => {
        if (e.target === backdropRef.current) setOpen(false);
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-modal-title"
        className="w-full max-w-2xl mx-4 bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col max-h-[85vh] animate-fade-slide-up"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-8 pt-7 pb-2">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-primary text-2xl" aria-hidden="true">
              tune
            </span>
            <h2 id="settings-modal-title" className="text-xl font-bold text-text-main">
              Custom Instructions & Glossary
            </h2>
          </div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="p-2 text-text-muted hover:text-text-main hover:bg-slate-100 rounded-lg transition-colors"
          >
            <span className="material-symbols-outlined text-xl" aria-hidden="true">close</span>
          </button>
        </div>

        {/* No sheet selected — gate */}
        {!selectedSheet ? (
          <div className="flex-1 flex flex-col items-center justify-center px-8 py-16 text-center">
            <span className="material-symbols-outlined text-5xl text-slate-300 mb-4" aria-hidden="true">
              table_chart
            </span>
            <p className="text-base font-semibold text-text-main mb-1">
              No sheet selected
            </p>
            <p className="text-sm text-text-muted max-w-xs">
              Connect to a Google Sheet and select a tab first, then come back
              to configure prompts and glossary.
            </p>
          </div>
        ) : (
        <>
        {/* Tabs */}
        <div className="px-8 pt-4 pb-2">
          <div className="flex bg-slate-100/80 rounded-xl p-1.5 border border-slate-200" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={tab === "prompting"}
              onClick={() => setTab("prompting")}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all duration-200 ${
                tab === "prompting"
                  ? "bg-white text-primary shadow-sm"
                  : "text-slate-500 hover:text-text-main"
              }`}
            >
              AI Prompting
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === "glossary"}
              onClick={() => setTab("glossary")}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all duration-200 ${
                tab === "glossary"
                  ? "bg-white text-primary shadow-sm"
                  : "text-slate-500 hover:text-text-main"
              }`}
            >
              Glossary
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-8 py-5" role="tabpanel">
          {tab === "prompting" && (
            <div className="space-y-5">
              {/* Game Synopsis */}
              <div>
                <h3 className="text-base font-semibold text-text-main">
                  Game Synopsis
                </h3>
                <p className="text-sm text-text-muted mt-1">
                  Describe the game world, story, and key characters. This
                  context helps the AI understand the game and translate
                  accordingly.
                </p>
              </div>
              <textarea
                value={synopsisText}
                onChange={(e) => setSynopsisText(e.target.value)}
                placeholder="E.g., A space adventure game where Robot 404 delivers packages across the galaxy..."
                className="w-full h-28 rounded-xl border border-slate-200 bg-white p-4 text-sm text-text-main placeholder:text-slate-400 focus:ring-2 focus:ring-primary focus:border-transparent resize-none transition-all"
              />

              {/* Tone & Manner */}
              <div>
                <h3 className="text-base font-semibold text-text-main">
                  Tone & Manner
                </h3>
                <p className="text-sm text-text-muted mt-1">
                  Define the overall translation style and voice.
                </p>
              </div>
              <textarea
                value={toneText}
                onChange={(e) => setToneText(e.target.value)}
                placeholder="E.g., Humorous and casual tone. Avoid overly formal language..."
                className="w-full h-16 rounded-xl border border-slate-200 bg-white p-4 text-sm text-text-main placeholder:text-slate-400 focus:ring-2 focus:ring-primary focus:border-transparent resize-none transition-all"
              />

              {/* Custom Instructions (per sheet) */}
              <div>
                <h3 className="text-base font-semibold text-text-main">
                  Custom AI Instructions
                </h3>
                <p className="text-sm text-text-muted mt-1">
                  Additional rules for the AI translator, specific to this
                  sheet.
                  {selectedSheet && (
                    <span className="ml-1 text-primary font-medium">
                      ({selectedSheet})
                    </span>
                  )}
                </p>
              </div>
              <textarea
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                placeholder="E.g., Translate with a medieval fantasy tone. Use formal pronouns for characters. Avoid modern slang..."
                className="w-full h-28 rounded-xl border border-slate-200 bg-white p-4 text-sm text-text-main placeholder:text-slate-400 focus:ring-2 focus:ring-primary focus:border-transparent resize-none transition-all"
              />
              <div className="flex items-start gap-2 text-xs text-text-muted bg-blue-50/50 p-3 rounded-lg border border-blue-100/50">
                <span className="material-symbols-outlined text-sm text-primary mt-0.5" aria-hidden="true">
                  info
                </span>
                <span>
                  Synopsis and Tone are global settings shared across all
                  sheets. Custom Instructions are saved per sheet tab.
                </span>
              </div>
            </div>
          )}

          {tab === "glossary" && (
            <div className="space-y-5">
              <div>
                <h3 className="text-base font-semibold text-text-main">
                  Translation Glossary
                </h3>
                <p className="text-sm text-text-muted mt-1">
                  Define fixed translations for specific terms. These are
                  enforced during translation and post-processing.
                </p>
              </div>

              {/* Language selector */}
              <div className="flex gap-2">
                {(Object.keys(LANG_LABELS) as GlossaryLang[]).map((lang) => (
                  <button
                    type="button"
                    key={lang}
                    onClick={() => setGlossaryLang(lang)}
                    className={`px-4 py-2 text-sm font-medium rounded-lg border transition-all duration-200 ${
                      glossaryLang === lang
                        ? "bg-primary/10 border-primary/30 text-primary"
                        : "bg-white border-slate-200 text-text-muted hover:border-slate-300 hover:text-text-main"
                    }`}
                  >
                    {LANG_LABELS[lang]}
                  </button>
                ))}
              </div>

              {/* Add new entry */}
              <div className="flex gap-3 items-end">
                <div className="flex-1">
                  <label className="block text-xs font-medium text-text-muted mb-1.5">
                    Source (KO)
                  </label>
                  <input
                    type="text"
                    value={newSource}
                    onChange={(e) => setNewSource(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAddEntry()}
                    placeholder="e.g., ..."
                    className="w-full rounded-lg border border-slate-200 bg-white py-2.5 px-3 text-sm text-text-main placeholder:text-slate-400 focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                  />
                </div>
                <span className="text-slate-300 font-medium pb-2.5">{"\u2192"}</span>
                <div className="flex-1">
                  <label className="block text-xs font-medium text-text-muted mb-1.5">
                    Target ({glossaryLang.toUpperCase()})
                  </label>
                  <input
                    type="text"
                    value={newTarget}
                    onChange={(e) => setNewTarget(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAddEntry()}
                    placeholder={
                      glossaryLang === "ja" ? "e.g., \u4F1D\u8AAC" : "e.g., Legend"
                    }
                    className="w-full rounded-lg border border-slate-200 bg-white py-2.5 px-3 text-sm text-text-main placeholder:text-slate-400 focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleAddEntry}
                  disabled={!newSource.trim() || !newTarget.trim()}
                  className="shrink-0 p-2.5 rounded-lg bg-primary text-white hover:bg-primary-dark disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <span className="material-symbols-outlined text-lg" aria-hidden="true">add</span>
                </button>
              </div>

              {/* Glossary table */}
              {currentEntries.length > 0 ? (
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200">
                        <th scope="col" className="text-left py-2.5 px-4 font-semibold text-text-muted text-xs uppercase tracking-wider">
                          Source (KO)
                        </th>
                        <th scope="col" className="text-left py-2.5 px-4 font-semibold text-text-muted text-xs uppercase tracking-wider">
                          Target ({glossaryLang.toUpperCase()})
                        </th>
                        <th scope="col" className="w-12" />
                      </tr>
                    </thead>
                    <tbody>
                      {currentEntries.map(([source, target]) => (
                        <tr
                          key={source}
                          className="border-b border-slate-100 last:border-0 hover:bg-slate-50/50 transition-colors"
                        >
                          <td className="py-2.5 px-4 text-text-main font-medium">
                            {source}
                          </td>
                          <td className="py-2.5 px-4 text-text-main">
                            {target}
                          </td>
                          <td className="py-2.5 px-2">
                            <button
                              type="button"
                              onClick={() => handleDeleteEntry(source)}
                              className="p-1 text-slate-400 hover:text-red-500 rounded transition-colors"
                            >
                              <span className="material-symbols-outlined text-base" aria-hidden="true">
                                delete
                              </span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-10 text-text-muted text-sm border border-dashed border-slate-200 rounded-xl">
                  <span className="material-symbols-outlined text-3xl text-slate-300 mb-2 block" aria-hidden="true">
                    book_2
                  </span>
                  No glossary entries for {LANG_LABELS[glossaryLang]} yet.
                  <br />
                  Add terms above to enforce consistent translations.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-8 py-5 border-t border-slate-100">
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="px-6 py-2.5 text-sm font-medium text-text-muted hover:text-text-main transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2.5 text-sm font-bold text-white bg-primary hover:bg-primary-dark rounded-xl transition-colors disabled:opacity-50 shadow-sm"
          >
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>
        </>
        )}
      </div>
    </div>
  );
}
