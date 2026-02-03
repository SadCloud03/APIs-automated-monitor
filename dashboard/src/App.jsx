import React, { useEffect, useMemo, useState } from "react";
import { addApi, deleteApi, getApis, getLogs, getOverview, uploadApisTxt } from "./api.js";

function StatusBadge({ s }) {
  const cls = s === "UP" ? "badge up" : s === "DOWN" ? "badge down" : "badge";
  return <span className={cls}>{s || "UNKNOWN"}</span>;
}

function SineWave({ latency, seed = 0, status }) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    if (status === "DOWN") return; // ⛔ no animar si está caído

    let raf = 0;
    const tick = () => {
      setPhase((Date.now() / 1000) * 2 + seed * 0.9);
      raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [seed, status]);

  const w = 120;
  const h = 24;
  const mid = h / 2;

  const baseAmp = 6;
  const amp =
    status === "DOWN"
      ? 0 // 📉 línea plana
      : Math.max(2, Math.min(10, baseAmp + (Number(latency) || 0) * 10));

  const points = [];
  const steps = 48;

  for (let i = 0; i <= steps; i++) {
    const x = (i / steps) * w;
    const y = mid + amp * Math.sin((i / steps) * Math.PI * 2 + phase);
    points.push(`${x.toFixed(2)},${y.toFixed(2)}`);
  }

  return (
    <svg
      className={`wave ${status === "DOWN" ? "wave-down" : "wave-up"}`}
      width={w}
      height={h}
      viewBox={`0 0 ${w} ${h}`}
      aria-hidden="true"
    >
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      />
    </svg>
  );
}


export default function App() {
  const [overview, setOverview] = useState({ total: 0, up: 0, down: 0 });
  const [apis, setApis] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [logs, setLogs] = useState([]);
  const [err, setErr] = useState("");

  const [name, setName] = useState("");
  const [url, setUrl] = useState("");

  const [txtFile, setTxtFile] = useState(null);
  const [uploadMsg, setUploadMsg] = useState("");
  const [fileKey, setFileKey] = useState(0);

  async function refresh() {
    setErr("");
    try {
      const [ov, list] = await Promise.all([getOverview(), getApis()]);
      setOverview(ov);
      setApis(list);

      if (selectedId) {
        const l = await getLogs(selectedId, 200);
        setLogs(l);
      }
    } catch (e) {
      setErr(String(e?.message || e));
    }
  }

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  const selectedApi = useMemo(
    () => apis.find((a) => a.id === selectedId) || null,
    [apis, selectedId]
  );

  async function onAdd(e) {
    e.preventDefault();
    setErr("");
    try {
      await addApi(name.trim(), url.trim());
      setName("");
      setUrl("");
      await refresh();
    } catch (e2) {
      setErr(String(e2?.message || e2));
    }
  }

  async function onDelete(apiId) {
    setErr("");
    try {
      await deleteApi(apiId);
      if (selectedId === apiId) {
        setSelectedId(null);
        setLogs([]);
      }
      await refresh();
    } catch (e2) {
      setErr(String(e2?.message || e2));
    }
  }

  async function onUploadTxt(e) {
    e.preventDefault();
    setErr("");
    setUploadMsg("");

    if (!txtFile) {
      setUploadMsg("Elegí un archivo .txt primero.");
      return;
    }

    try {
      setUploadMsg("Subiendo...");
      const res = await uploadApisTxt(txtFile);
      setUploadMsg(`OK: agregadas ${res.added} | saltadas ${res.skipped}`);
      setTxtFile(null);
      setFileKey((k) => k + 1);
      await refresh();
    } catch (e2) {
      setErr(String(e2?.message || e2));
      setUploadMsg("");
    }
  }

  return (
    <div className="wrap">
      <header className="topbar">
        <h1>API Monitor Dashboard</h1>
        <div className="kpis">
          <div className="kpi">
            <div className="kpiLabel">Total</div>
            <div className="kpiValue">{overview.total}</div>
          </div>
          <div className="kpi">
            <div className="kpiLabel">UP</div>
            <div className="kpiValue">{overview.up}</div>
          </div>
          <div className="kpi">
            <div className="kpiLabel">DOWN</div>
            <div className="kpiValue">{overview.down}</div>
          </div>
        </div>
      </header>

      {err ? <div className="error">{err}</div> : null}

      <main className="grid">
        <section className="card">
          <h2>APIs</h2>

          <form className="row" onSubmit={onAdd}>
            <input
              placeholder="Nombre"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <input
              placeholder="URL https://..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
            <button type="submit">Agregar</button>
          </form>

          <form className="row" onSubmit={onUploadTxt}>
            <input
              key={fileKey}
              type="file"
              accept=".txt"
              onChange={(e) => setTxtFile(e.target.files?.[0] || null)}
            />
            <button type="submit" disabled={!txtFile}>Subir TXT</button>
          </form>

          <div className="muted" style={{ marginBottom: 10 }}>
            {txtFile ? `Archivo: ${txtFile.name} (${txtFile.size} bytes)` : "Elegí un .txt para cargar muchas APIs."}
          </div>

          {uploadMsg ? (
            <div className="muted" style={{ marginBottom: 10 }}>
              {uploadMsg}
            </div>
          ) : null}

          <table className="table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Nombre</th>
                <th>Latency</th>
                <th>Último check</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {apis.map((a) => (
                <tr
                  key={a.id}
                  className={selectedId === a.id ? "selected" : ""}
                  onClick={() => setSelectedId(a.id)}
                  title={a.url}
                >
                  <td><StatusBadge s={a.last_status} /></td>
                  <td className="mono">{a.name}</td>
                  <td>
                      <div>{a.last_latency != null ? `${a.last_latency}s` : "—"}</div>
                      <SineWave
                        latency={a.last_latency}
                        seed={a.id}
                        status={a.last_status}
                      />
                  </td>

                  <td className="mono">{a.last_checked_at || "—"}</td>
                  <td>
                    <button
                      className="danger"
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(a.id);
                      }}
                    >
                      Borrar
                    </button>
                  </td>
                </tr>
              ))}
              {!apis.length ? (
                <tr><td colSpan="5">No hay APIs cargadas.</td></tr>
              ) : null}
            </tbody>
          </table>
        </section>

        <section className="card">
          <h2>Logs</h2>
          {selectedApi ? (
            <div className="sub">
              <div><b>{selectedApi.name}</b></div>
              <div className="mono">{selectedApi.url}</div>
            </div>
          ) : (
            <div className="muted">Seleccioná una API para ver logs.</div>
          )}

          <div className="logs">
            {logs.map((l) => (
              <div key={l.id} className="logRow">
                <div className="mono">{l.timestamp}</div>
                <div><StatusBadge s={l.status} /></div>
                <div className="mono">code={l.status_code ?? "—"}</div>
                <div className="mono">lat={l.latency ?? "—"}</div>
                <div className="mono clip">{l.response ?? ""}</div>
              </div>
            ))}
            {selectedApi && !logs.length ? (
              <div className="muted">Sin logs todavía.</div>
            ) : null}
          </div>
        </section>
      </main>

      <footer className="footer">
        Backend: <span className="mono">http://localhost:8001</span> • Polling 5s
      </footer>
    </div>
  );
}
