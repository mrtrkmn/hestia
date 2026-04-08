import { useTranslation } from "react-i18next";

const LANGS = [
  { code: "en", label: "EN" },
  { code: "tr", label: "TR" },
  { code: "de", label: "DE" },
];

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const change = (lng: string) => {
    i18n.changeLanguage(lng);
    localStorage.setItem("hestia_lang", lng);
  };

  return (
    <div style={{ display: "flex", gap: 2, marginLeft: "auto" }}>
      {LANGS.map((l) => (
        <button
          key={l.code}
          onClick={() => change(l.code)}
          style={{
            padding: "4px 8px",
            fontSize: 12,
            fontWeight: i18n.language === l.code ? 700 : 400,
            background: i18n.language === l.code ? "#1e2030" : "transparent",
            color: i18n.language === l.code ? "#e1e1e6" : "#a0a3b1",
            border: "none",
            borderRadius: 4,
            cursor: "pointer",
          }}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
