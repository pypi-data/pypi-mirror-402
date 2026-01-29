import { useState, useEffect } from 'react'
import { Activity, AlertTriangle, BarChart3, ChevronRight, LayoutDashboard, Shield, TrendingUp } from 'lucide-react'
import clsx from 'clsx'

// Types matching API
interface RunSummary {
    run_id: string
    as_of: string
    strategy_name: string
}

interface Report {
    run_id: string
    created_at: string
    data: {
        strategy: { name: string; universe: string }
        artifacts: Array<{
            type: string
            name: string
            payload: any
        }>
        assumption_map: {
            assumptions: Array<{
                assumption_id: string
                title: string
                severity: string
                confidence: number
                description: string
            }>
            triggers: Array<{
                title: string
                severity: string
                condition: string
            }>
        }
    }
}

const API_BASE = 'http://127.0.0.1:8000'

function App() {
    const [runs, setRuns] = useState<RunSummary[]>([])
    const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
    const [report, setReport] = useState<Report | null>(null)
    const [loading, setLoading] = useState(false)

    // Fetch runs on load
    useEffect(() => {
        fetch(`${API_BASE}/runs`)
            .then(res => res.json())
            .then(data => {
                setRuns(data)
                if (data.length > 0) setSelectedRunId(data[0].run_id)
            })
            .catch(err => console.error("Failed to fetch runs:", err))
    }, [])

    // Fetch report when run selected
    useEffect(() => {
        if (!selectedRunId) return
        setLoading(true)
        fetch(`${API_BASE}/runs/${selectedRunId}`)
            .then(res => res.json())
            .then(data => {
                setReport(data)
                setLoading(false)
            })
            .catch(err => {
                console.error("Failed to fetch report:", err)
                setLoading(false)
            })
    }, [selectedRunId])

    // Helpers to extract metrics
    const getMetric = (name: string) => {
        const a = report?.data.artifacts.find(x => x.name === name && x.type === 'metric')
        return a ? a.payload.value : null
    }

    const formatVal = (val: number | null, isPct = false) => {
        if (val === null) return 'N/A'
        return isPct ? `${(val * 100).toFixed(1)}%` : val.toFixed(2)
    }

    return (
        <div className="flex h-screen overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 bg-[#0f1722] border-r border-gray-800 flex flex-col">
                <div className="p-6">
                    <div className="flex items-center gap-2 text-blue-400 font-bold text-xl">
                        <Shield className="w-6 h-6" />
                        <span>Robustlabs</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1 uppercase tracking-wider font-medium">Mark 2 Dashboard</div>
                </div>

                <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
                    <div className="text-xs text-gray-500 px-3 py-2 font-semibold uppercase">Recent Runs</div>
                    {runs.map(run => (
                        <button
                            key={run.run_id}
                            onClick={() => setSelectedRunId(run.run_id)}
                            className={clsx(
                                "w-full text-left px-3 py-3 rounded-lg text-sm transition-colors flex flex-col gap-1",
                                selectedRunId === run.run_id
                                    ? "bg-blue-900/20 text-blue-400 border border-blue-800/30"
                                    : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
                            )}
                        >
                            <span className="font-medium text-white truncate">{run.strategy_name}</span>
                            <span className="text-xs opacity-70 truncate">{run.run_id.slice(0, 8)}...</span>
                        </button>
                    ))}
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto bg-[#0b0f14] p-8">
                {loading || !report ? (
                    <div className="h-full flex items-center justify-center text-gray-500 animate-pulse">
                        Loading decision context...
                    </div>
                ) : (
                    <div className="max-w-6xl mx-auto space-y-8">

                        {/* Header */}
                        <div className="flex justify-between items-end">
                            <div>
                                <h1 className="text-3xl font-bold text-white">{report.data.strategy.name}</h1>
                                <p className="text-gray-400 mt-2 flex items-center gap-2">
                                    <span className="bg-gray-800 px-2 py-0.5 rounded text-xs font-mono">{report.run_id}</span>
                                    <span>•</span>
                                    <span>{new Date(report.created_at || new Date()).toLocaleDateString()}</span>
                                </p>
                            </div>
                            <div className="flex gap-3">
                                <button className="btn-primary flex items-center gap-2">
                                    <LayoutDashboard className="w-4 h-4" /> View Full Report
                                </button>
                            </div>
                        </div>

                        {/* KPI Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <MetricCard
                                label="CAGR"
                                value={formatVal(getMetric('cagr'), true)}
                                icon={<TrendingUp className="w-5 h-5 text-emerald-400" />}
                            />
                            <MetricCard
                                label="Max Drawdown"
                                value={formatVal(getMetric('max_drawdown'), true)}
                                icon={<Activity className="w-5 h-5 text-rose-400" />}
                            />
                            <MetricCard
                                label="Tail Amplification"
                                value={formatVal(getMetric('tail_amplification'))}
                                icon={<AlertTriangle className="w-5 h-5 text-amber-400" />}
                                highlight={(getMetric('tail_amplification') || 0) > 2.5}
                            />
                            <MetricCard
                                label="Timing Sensitivity"
                                value={formatVal(getMetric('timing_sensitivity'))}
                                icon={<BarChart3 className="w-5 h-5 text-blue-400" />}
                            />
                        </div>

                        {/* Triggers */}
                        {report.data.assumption_map.triggers.length > 0 && (
                            <div className="bg-red-900/10 border border-red-800/30 rounded-xl p-6">
                                <h3 className="text-red-400 font-bold flex items-center gap-2 mb-4">
                                    <AlertTriangle className="w-5 h-5" /> Review Triggers Active
                                </h3>
                                <div className="space-y-3">
                                    {report.data.assumption_map.triggers.map((t, i) => (
                                        <div key={i} className="flex gap-4 p-3 bg-red-900/20 rounded-lg border border-red-800/20">
                                            <div className="font-bold text-red-200 uppercase text-xs tracking-wider mt-1">{t.severity}</div>
                                            <div>
                                                <div className="font-semibold text-red-100">{t.title}</div>
                                                <div className="text-sm text-red-300 font-mono mt-1">{t.condition}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Assumption Map */}
                        <section>
                            <h2 className="text-xl font-bold text-white mb-4">Assumption Map</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {report.data.assumption_map.assumptions.map((a) => (
                                    <div key={a.assumption_id} className="card relative group">
                                        <div className="absolute top-4 right-4 text-xs font-bold text-gray-500 group-hover:text-gray-300">
                                            CONFIDENCE: {(a.confidence * 100).toFixed(0)}%
                                        </div>
                                        <div className="flex items-center gap-2 mb-3">
                                            <span className={clsx(
                                                "w-2 h-2 rounded-full",
                                                a.severity === 'critical' ? "bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]" :
                                                    a.severity === 'high' ? "bg-orange-500" :
                                                        a.severity === 'medium' ? "bg-yellow-500" :
                                                            "bg-green-500"
                                            )} />
                                            <span className="font-mono text-xs text-gray-400">{a.assumption_id}</span>
                                        </div>
                                        <h3 className="font-bold text-lg mb-2 leading-tight">{a.title}</h3>
                                        <p className="text-sm text-gray-400 leading-relaxed mb-4">{a.description}</p>

                                        <div className="border-t border-gray-800 pt-3 mt-auto">
                                            <div className="flex justify-between items-center text-xs text-gray-500">
                                                <span>SEVERITY: <span className="text-gray-300 uppercase">{a.severity}</span></span>
                                                <ChevronRight className="w-4 h-4" />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>

                        {/* Evidence (Regimes) */}
                        <section>
                            <h2 className="text-xl font-bold text-white mb-4">Regime Performance</h2>
                            {(() => {
                                const table = report.data.artifacts.find(a => a.name === 'regime_performance');
                                if (!table) return <div className="text-gray-500 font-mono">No regime data found.</div>;

                                const rows = table.payload.rows || [];
                                const headers = rows.length ? Object.keys(rows[0]) : [];

                                return (
                                    <div className="card overflow-x-auto">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr>
                                                    {headers.map(h => (
                                                        <th key={h} className="p-3 border-b border-gray-800 text-xs font-bold text-gray-400 uppercase tracking-wider">{h}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {rows.map((row: any, idx: number) => (
                                                    <tr key={idx} className="group hover:bg-white/5 transition-colors">
                                                        {headers.map(h => (
                                                            <td key={h} className="p-3 border-b border-gray-800 text-sm text-gray-300 font-mono group-hover:text-white">
                                                                {typeof row[h] === 'number' ? row[h].toFixed(2) : row[h]}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )
                            })()}
                        </section>

                    </div>
                )}
            </main>
        </div>
    )
}

function MetricCard({ label, value, icon, highlight = false }: { label: string, value: string, icon: any, highlight?: boolean }) {
    return (
        <div className={clsx("card flex items-center justify-between", highlight && "border-amber-500/50 bg-amber-500/5")}>
            <div>
                <div className="text-xs text-gray-500 uppercase font-semibold tracking-wider mb-1">{label}</div>
                <div className="text-2xl font-bold text-white font-mono">{value}</div>
            </div>
            <div className="bg-gray-800/50 p-2 rounded-lg">{icon}</div>
        </div>
    )
}

export default App
