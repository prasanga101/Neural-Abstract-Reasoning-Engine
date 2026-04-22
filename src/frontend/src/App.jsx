import { useState } from 'react'
import './App.css'
import { FlowCanvas } from './components/flow/FlowCanvas'
import { mockPipelineData } from './data/mockPipelineData'
import { normalizePipelineData } from './data/pipelineDataAdapter'

function getErrorMessage(payload, fallbackMessage) {
  if (!payload) return fallbackMessage

  if (typeof payload.detail === 'string') return payload.detail
  if (payload.detail?.message) return payload.detail.message
  if (payload.message) return payload.message

  return fallbackMessage
}

function App() {
  const [emergencyText, setEmergencyText] = useState(
    'A major earthquake has struck Pokhara, Nepal. Thousands of people have been displaced, critical injuries are being reported across multiple areas, and immediate medical response, shelter allocation, and route coordination are urgently needed.'
  )
  const [threshold, setThreshold] = useState(75)
  const [runSignal, setRunSignal] = useState(0)
  const [pipelineInspectorSignal, setPipelineInspectorSignal] = useState(0)
  const [pipelineData, setPipelineData] = useState(() =>
    normalizePipelineData(mockPipelineData)
  )
  const [isRunning, setIsRunning] = useState(false)
  const [apiStatus, setApiStatus] = useState('Backend disconnected. Click Run to fetch a live pipeline output.')
  const [apiError, setApiError] = useState('')

  const handleRun = async () => {
    const prompt = emergencyText.trim()

    if (!prompt) {
      setApiError('Enter an emergency prompt before running the pipeline.')
      return
    }

    setIsRunning(true)
    setApiError('')
    setApiStatus('Running backend pipeline...')

    try {
      const response = await fetch('/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: prompt,
          threshold: threshold / 100,
        }),
      })

      const payload = await response.json()

      if (!response.ok) {
        throw new Error(getErrorMessage(payload, 'Backend pipeline request failed.'))
      }

      const nextData = normalizePipelineData(payload.output ?? payload)
      setPipelineData(nextData)
      setRunSignal((value) => value + 1)
      setApiStatus(
        payload.duration_ms != null
          ? `Backend run completed in ${payload.duration_ms} ms at threshold ${threshold}.`
          : 'Backend run completed successfully.'
      )
    } catch (error) {
      setApiError(error.message || 'Unable to reach the backend pipeline.')
      setApiStatus('Backend request failed.')
    } finally {
      setIsRunning(false)
    }
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

          <button
            type="button"
            onClick={handleRun}
            className="run-button"
            disabled={isRunning}
          >
            {isRunning ? 'Running...' : 'Run'}
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
      <div
        className={`api-status ${apiError ? 'api-status--error' : ''}`}
        role="status"
        aria-live="polite"
      >
        {apiError || apiStatus}
      </div>
      <FlowCanvas
        data={pipelineData}
        runSignal={runSignal}
        pipelineInspectorSignal={pipelineInspectorSignal}
      />
    </main>
  )
}

export default App
