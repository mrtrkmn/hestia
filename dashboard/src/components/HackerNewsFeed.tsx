import { useState, useEffect } from "react";

interface HNItem {
  id: number;
  title: string;
  url: string;
  score: number;
  by: string;
  time: number;
}

const API = "https://hacker-news.firebaseio.com/v0";

export default function HackerNewsFeed() {
  const [items, setItems] = useState<HNItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const ids: number[] = await fetch(`${API}/topstories.json`).then((r) => r.json());
        const stories = await Promise.all(
          ids.slice(0, 8).map((id) => fetch(`${API}/item/${id}.json`).then((r) => r.json()))
        );
        setItems(stories);
      } catch { /* offline */ }
      setLoading(false);
    };
    load();
    const id = setInterval(load, 300000);
    return () => clearInterval(id);
  }, []);

  const timeAgo = (ts: number) => {
    const m = Math.floor((Date.now() / 1000 - ts) / 60);
    if (m < 60) return `${m}m`;
    const h = Math.floor(m / 60);
    return h < 24 ? `${h}h` : `${Math.floor(h / 24)}d`;
  };

  const domain = (url: string) => {
    try { return new URL(url).hostname.replace("www.", ""); } catch { return ""; }
  };

  return (
    <div className="card" style={{ padding: 0, overflow: "hidden" }}>
      <div style={{ padding: "14px 18px 10px", borderBottom: "1px solid #1e2540", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: "#e8eaf0" }}>
          <span style={{ color: "#f97316", marginRight: 6 }}>Y</span>Hacker News
        </span>
        <a href="https://news.ycombinator.com/" target="_blank" rel="noopener" style={{ fontSize: 11, color: "#4a5178" }}>View all →</a>
      </div>
      {loading ? (
        <div style={{ padding: 24, textAlign: "center", color: "#4a5178", fontSize: 13 }}>Loading…</div>
      ) : items.length === 0 ? (
        <div style={{ padding: 24, textAlign: "center", color: "#4a5178", fontSize: 13 }}>Could not load feed.</div>
      ) : (
        <div>{items.map((item, i) => (
          <a key={item.id} href={item.url || `https://news.ycombinator.com/item?id=${item.id}`} target="_blank" rel="noopener"
            style={{ display: "flex", gap: 12, padding: "10px 18px", borderBottom: i < items.length - 1 ? "1px solid rgba(30,37,64,0.5)" : "none", textDecoration: "none", transition: "background 0.1s", alignItems: "flex-start" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(22,27,46,0.6)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
            <span style={{ color: "#f97316", fontSize: 12, fontWeight: 700, minWidth: 28, textAlign: "right", paddingTop: 2 }}>{item.score}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, color: "#c0c4d8", lineHeight: 1.4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.title}</div>
              <div style={{ fontSize: 11, color: "#4a5178", marginTop: 2 }}>
                {item.url && <span style={{ marginRight: 8 }}>{domain(item.url)}</span>}
                <span>{item.by}</span><span style={{ margin: "0 4px" }}>·</span><span>{timeAgo(item.time)}</span>
              </div>
            </div>
          </a>
        ))}</div>
      )}
    </div>
  );
}
