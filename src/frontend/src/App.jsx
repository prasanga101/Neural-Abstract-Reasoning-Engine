import { useState } from 'react'
import './App.css'
import { FlowCanvas } from './components/flow/FlowCanvas'
import { mockPipelineData } from './data/mockPipelineData'
import { normalizePipelineData, pipelineDataFromInput } from './data/pipelineDataAdapter'

function App() {
  const [emergencyText, setEmergencyText] = useState(
    'Flash flooding reported near Riverside district. Need evacuation guidance.'
  )
  const [threshold, setThreshold] = useState(75)
  const [runSignal, setRunSignal] = useState(0)
  const [pipelineInspectorSignal, setPipelineInspectorSignal] = useState(0)
  const [pipelineData, setPipelineData] = useState(() =>
    normalizePipelineData(mockPipelineData)
  )

  const handleRun = () => {
    const next = pipelineDataFromInput(emergencyText, pipelineData)
    setPipelineData(next.data)
    setRunSignal((value) => value + 1)
  }

  return (
    <main className="app-shell">
      <nav className="top-nav" aria-label="NARE controls">
        <a className="brand" aria-label="Go to NARE homepage" href="/">
          <span className="brand-mark" aria-hidden="true">
            ✦
          </span>
          <div className="brand-text">
            <strong>NARE | Neural Abstract Reasoning Engine</strong>
            <small>Disaster Response Intelligence</small>
          </div>
        </a>

        <div className="center-controls">
          <input
            type="text"
            value={emergencyText}
            onChange={(event) => setEmergencyText(event.target.value)}
            placeholder="Describe the emergency situation..."
            aria-label="Emergency text input"
          />
        </div>

        <div className="right-controls">
          <button
            type="button"
            className="pipeline-inspector-button"
            onClick={() => setPipelineInspectorSignal((value) => value + 1)}
          >
            <span className="pipeline-inspector-dots" aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
            </span>
            Pipeline Phases
          </button>

          <button type="button" onClick={handleRun}>
            Run
          </button>

          <div className="threshold-control">
            <label htmlFor="threshold">Threshold</label>
            <input
              id="threshold"
              type="range"
              min="0"
              max="100"
              value={threshold}
              onChange={(event) => setThreshold(Number(event.target.value))}
            />
            <span>{threshold}</span>
          </div>
        </div>
      </nav>
      <FlowCanvas
        data={pipelineData}
        runSignal={runSignal}
        pipelineInspectorSignal={pipelineInspectorSignal}
      />
    </main>
  )
}

export default App
