import { useTranslation } from "react-i18next";

const LANGS = [
  { code: "en", label: "EN", flag: "🇬🇧" },
  { code: "tr", label: "TR", flag: "🇹🇷" },
  { code: "de", label: "DE", flag: "🇩🇪" },
];

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const change = (lng: string) => {
    i18n.changeLanguage(lng);
    localStorage.setItem("hestia_lang", lng);
  };

  return (
    <div style={{ display: "flex", gap: 4 }}>
      {LANGS.map((l) => (
        <button
          key={l.code}
          onClick={() => change(l.code)}
          className={`btn btn-sm ${i18n.language === l.code ? "btn-primary" : "btn-ghost"}`}
          style={{ minWidth: 40 }}
          title={l.label}
        >
          {l.flag}
        </button>
      ))}
    </div>
  );
}
